from typing import Any, Iterable, List, Mapping, Optional, Set, Tuple, Union

from django.conf import settings
from django.db.models.query import QuerySet
from django.utils.translation import ugettext as _

from zerver.lib.bugdown import convert as bugdown_convert
from zerver.lib.request import JsonableError
from zerver.models import (
    DefaultStreamGroup,
    Realm,
    Recipient,
    Stream,
    Subscription,
    UserProfile,
    active_non_guest_user_ids,
    bulk_get_streams,
    get_realm_stream,
    get_stream,
    get_stream_by_id_in_realm,
    is_cross_realm_bot_email,
)
from zerver.tornado.event_queue import send_event


def get_default_value_for_history_public_to_subscribers(
        realm: Realm,
        invite_only: bool,
        history_public_to_subscribers: Optional[bool],
) -> bool:
    if invite_only:
        if history_public_to_subscribers is None:
            # A private stream's history is non-public by default
            history_public_to_subscribers = False
    else:
        # If we later decide to support public streams without
        # history, we can remove this code path.
        history_public_to_subscribers = True

    if realm.is_zephyr_mirror_realm:
        # In the Zephyr mirroring model, history is unconditionally
        # not public to subscribers, even for public streams.
        history_public_to_subscribers = False

    return history_public_to_subscribers

def render_stream_description(text: str) -> str:
    return bugdown_convert(text, no_previews=True)

def send_stream_creation_event(stream: Stream, user_ids: List[int]) -> None:
    event = dict(type="stream", op="create",
                 streams=[stream.to_dict()])
    send_event(stream.realm, event, user_ids)

def create_stream_if_needed(realm: Realm,
                            stream_name: str,
                            *,
                            invite_only: bool=False,
                            stream_post_policy: int=Stream.STREAM_POST_POLICY_EVERYONE,
                            history_public_to_subscribers: Optional[bool]=None,
                            stream_description: str="") -> Tuple[Stream, bool]:
    history_public_to_subscribers = get_default_value_for_history_public_to_subscribers(
        realm, invite_only, history_public_to_subscribers)

    (stream, created) = Stream.objects.get_or_create(
        realm=realm,
        name__iexact=stream_name,
        defaults = dict(
            name=stream_name,
            description=stream_description,
            invite_only=invite_only,
            stream_post_policy=stream_post_policy,
            history_public_to_subscribers=history_public_to_subscribers,
            is_in_zephyr_realm=realm.is_zephyr_mirror_realm,
        ),
    )

    if created:
        recipient = Recipient.objects.create(type_id=stream.id, type=Recipient.STREAM)

        stream.recipient = recipient
        stream.rendered_description = render_stream_description(stream_description)
        stream.save(update_fields=["recipient", "rendered_description"])

        if stream.is_public():
            send_stream_creation_event(stream, active_non_guest_user_ids(stream.realm_id))
        else:
            realm_admin_ids = [user.id for user in
                               stream.realm.get_admin_users_and_bots()]
            send_stream_creation_event(stream, realm_admin_ids)
    return stream, created

def create_streams_if_needed(realm: Realm,
                             stream_dicts: List[Mapping[str, Any]]) -> Tuple[List[Stream], List[Stream]]:
    """Note that stream_dict["name"] is assumed to already be stripped of
    whitespace"""
    added_streams: List[Stream] = []
    existing_streams: List[Stream] = []
    for stream_dict in stream_dicts:
        stream, created = create_stream_if_needed(
            realm,
            stream_dict["name"],
            invite_only=stream_dict.get("invite_only", False),
            stream_post_policy=stream_dict.get("stream_post_policy", Stream.STREAM_POST_POLICY_EVERYONE),
            history_public_to_subscribers=stream_dict.get("history_public_to_subscribers"),
            stream_description=stream_dict.get("description", ""),
        )

        if created:
            added_streams.append(stream)
        else:
            existing_streams.append(stream)

    return added_streams, existing_streams

def check_stream_name(stream_name: str) -> None:
    if stream_name.strip() == "":
        raise JsonableError(_("Invalid stream name '%s'") % (stream_name,))
    if len(stream_name) > Stream.MAX_NAME_LENGTH:
        raise JsonableError(_("Stream name too long (limit: %s characters).") % (Stream.MAX_NAME_LENGTH,))
    for i in stream_name:
        if ord(i) == 0:
            raise JsonableError(_("Stream name '%s' contains NULL (0x00) characters.") % (stream_name,))

def subscribed_to_stream(user_profile: UserProfile, stream_id: int) -> bool:
    return Subscription.objects.filter(
        user_profile=user_profile,
        active=True,
        recipient__type=Recipient.STREAM,
        recipient__type_id=stream_id).exists()

def access_stream_for_send_message(sender: UserProfile,
                                   stream: Stream,
                                   forwarder_user_profile: Optional[UserProfile]) -> None:
    # Our caller is responsible for making sure that `stream` actually
    # matches the realm of the sender.

    # Organization admins can send to any stream, irrespective of the stream_post_policy value.
    if sender.is_realm_admin or is_cross_realm_bot_email(sender.delivery_email):
        pass
    elif sender.is_bot and (sender.bot_owner is not None and
                            sender.bot_owner.is_realm_admin):
        pass
    elif stream.stream_post_policy == Stream.STREAM_POST_POLICY_ADMINS:
        raise JsonableError(_("Only organization administrators can send to this stream."))
    elif stream.stream_post_policy == Stream.STREAM_POST_POLICY_RESTRICT_NEW_MEMBERS:
        if sender.is_bot and (sender.bot_owner is not None and
                              sender.bot_owner.is_new_member):
            raise JsonableError(_("New members cannot send to this stream."))
        elif sender.is_new_member:
            raise JsonableError(_("New members cannot send to this stream."))

    if not (stream.invite_only or sender.is_guest):
        # This is a public stream and sender is not a guest user
        return

    if subscribed_to_stream(sender, stream.id):
        # It is private, but your are subscribed
        return

    if sender.is_api_super_user:
        return

    if (forwarder_user_profile is not None and forwarder_user_profile.is_api_super_user):
        return

    if sender.is_bot and (sender.bot_owner is not None and
                          subscribed_to_stream(sender.bot_owner, stream.id)):
        # Bots can send to any stream their owner can.
        return

    if sender.delivery_email == settings.WELCOME_BOT:
        # The welcome bot welcomes folks to the stream.
        return

    if sender.delivery_email == settings.NOTIFICATION_BOT:
        return

    # All other cases are an error.
    raise JsonableError(_("Not authorized to send to stream '%s'") % (stream.name,))

def check_for_exactly_one_stream_arg(stream_id: Optional[int], stream: Optional[str]) -> None:
    if stream_id is None and stream is None:
        raise JsonableError(_("Please supply 'stream'."))

    if stream_id is not None and stream is not None:
        raise JsonableError(_("Please choose one: 'stream' or 'stream_id'."))

def access_stream_for_delete_or_update(user_profile: UserProfile, stream_id: int) -> Stream:
    # We should only ever use this for realm admins, who are allowed
    # to delete or update all streams on their realm, even private streams
    # to which they are not subscribed.  We do an assert here, because
    # all callers should have the require_realm_admin decorator.
    assert(user_profile.is_realm_admin)

    error = _("Invalid stream id")
    try:
        stream = Stream.objects.get(id=stream_id)
    except Stream.DoesNotExist:
        raise JsonableError(error)

    if stream.realm_id != user_profile.realm_id:
        raise JsonableError(error)

    return stream

# Only set allow_realm_admin flag to True when you want to allow realm admin to
# access unsubscribed private stream content.
def access_stream_common(user_profile: UserProfile, stream: Stream,
                         error: str,
                         require_active: bool=True,
                         allow_realm_admin: bool=False) -> Tuple[Recipient, Optional[Subscription]]:
    """Common function for backend code where the target use attempts to
    access the target stream, returning all the data fetched along the
    way.  If that user does not have permission to access that stream,
    we throw an exception.  A design goal is that the error message is
    the same for streams you can't access and streams that don't exist."""

    # First, we don't allow any access to streams in other realms.
    if stream.realm_id != user_profile.realm_id:
        raise JsonableError(error)

    recipient = stream.recipient

    try:
        sub = Subscription.objects.get(user_profile=user_profile,
                                       recipient=recipient,
                                       active=require_active)
    except Subscription.DoesNotExist:
        sub = None

    # If the stream is in your realm and public, you can access it.
    if stream.is_public() and not user_profile.is_guest:
        return (recipient, sub)

    # Or if you are subscribed to the stream, you can access it.
    if sub is not None:
        return (recipient, sub)

    # For some specific callers (e.g. getting list of subscribers,
    # removing other users from a stream, and updating stream name and
    # description), we allow realm admins to access stream even if
    # they are not subscribed to a private stream.
    if user_profile.is_realm_admin and allow_realm_admin:
        return (recipient, sub)

    # Otherwise it is a private stream and you're not on it, so throw
    # an error.
    raise JsonableError(error)

def access_stream_by_id(user_profile: UserProfile,
                        stream_id: int,
                        require_active: bool=True,
                        allow_realm_admin: bool=False) -> Tuple[Stream, Recipient, Optional[Subscription]]:
    stream = get_stream_by_id(stream_id)

    error = _("Invalid stream id")
    (recipient, sub) = access_stream_common(user_profile, stream, error,
                                            require_active=require_active,
                                            allow_realm_admin=allow_realm_admin)
    return (stream, recipient, sub)

def get_public_streams_queryset(realm: Realm) -> 'QuerySet[Stream]':
    return Stream.objects.filter(realm=realm, invite_only=False,
                                 history_public_to_subscribers=True)

def get_stream_by_id(stream_id: int) -> Stream:
    error = _("Invalid stream id")
    try:
        stream = Stream.objects.get(id=stream_id)
    except Stream.DoesNotExist:
        raise JsonableError(error)
    return stream

def check_stream_name_available(realm: Realm, name: str) -> None:
    check_stream_name(name)
    try:
        get_stream(name, realm)
        raise JsonableError(_("Stream name '%s' is already taken.") % (name,))
    except Stream.DoesNotExist:
        pass

def access_stream_by_name(user_profile: UserProfile,
                          stream_name: str,
                          allow_realm_admin: bool=False) -> Tuple[Stream, Recipient, Optional[Subscription]]:
    error = _("Invalid stream name '%s'") % (stream_name,)
    try:
        stream = get_realm_stream(stream_name, user_profile.realm_id)
    except Stream.DoesNotExist:
        raise JsonableError(error)

    (recipient, sub) = access_stream_common(user_profile, stream, error,
                                            allow_realm_admin=allow_realm_admin)
    return (stream, recipient, sub)

def access_stream_for_unmute_topic_by_name(user_profile: UserProfile,
                                           stream_name: str,
                                           error: str) -> Stream:
    """
    It may seem a little silly to have this helper function for unmuting
    topics, but it gets around a linter warning, and it helps to be able
    to review all security-related stuff in one place.

    Our policy for accessing streams when you unmute a topic is that you
    don't necessarily need to have an active subscription or even "legal"
    access to the stream.  Instead, we just verify the stream_id has been
    muted in the past (not here, but in the caller).

    Long term, we'll probably have folks just pass us in the id of the
    MutedTopic row to unmute topics.
    """
    try:
        stream = get_stream(stream_name, user_profile.realm)
    except Stream.DoesNotExist:
        raise JsonableError(error)
    return stream

def access_stream_for_unmute_topic_by_id(user_profile: UserProfile,
                                         stream_id: int,
                                         error: str) -> Stream:
    try:
        stream = Stream.objects.get(id=stream_id, realm_id=user_profile.realm_id)
    except Stream.DoesNotExist:
        raise JsonableError(error)
    return stream

def can_access_stream_history(user_profile: UserProfile, stream: Stream) -> bool:
    """Determine whether the provided user is allowed to access the
    history of the target stream.  The stream is specified by name.

    This is used by the caller to determine whether this user can get
    historical messages before they joined for a narrowing search.

    Because of the way our search is currently structured,
    we may be passed an invalid stream here.  We return
    False in that situation, and subsequent code will do
    validation and raise the appropriate JsonableError.

    Note that this function should only be used in contexts where
    access_stream is being called elsewhere to confirm that the user
    can actually see this stream.
    """
    if stream.is_history_realm_public() and not user_profile.is_guest:
        return True

    if stream.is_history_public_to_subscribers():
        # In this case, we check if the user is subscribed.
        error = _("Invalid stream name '%s'") % (stream.name,)
        try:
            (recipient, sub) = access_stream_common(user_profile, stream, error)
        except JsonableError:
            return False
        return True
    return False

def can_access_stream_history_by_name(user_profile: UserProfile, stream_name: str) -> bool:
    try:
        stream = get_stream(stream_name, user_profile.realm)
    except Stream.DoesNotExist:
        return False
    return can_access_stream_history(user_profile, stream)

def can_access_stream_history_by_id(user_profile: UserProfile, stream_id: int) -> bool:
    try:
        stream = get_stream_by_id_in_realm(stream_id, user_profile.realm)
    except Stream.DoesNotExist:
        return False
    return can_access_stream_history(user_profile, stream)

def filter_stream_authorization(user_profile: UserProfile,
                                streams: Iterable[Stream]) -> Tuple[List[Stream], List[Stream]]:
    streams_subscribed: Set[int] = set()
    recipient_ids = [stream.recipient_id for stream in streams]
    subs = Subscription.objects.filter(user_profile=user_profile,
                                       recipient_id__in=recipient_ids,
                                       active=True)

    for sub in subs:
        streams_subscribed.add(sub.recipient.type_id)

    unauthorized_streams: List[Stream] = []
    for stream in streams:
        # The user is authorized for their own streams
        if stream.id in streams_subscribed:
            continue

        # Users are not authorized for invite_only streams, and guest
        # users are not authorized for any streams
        if stream.invite_only or user_profile.is_guest:
            unauthorized_streams.append(stream)

    authorized_streams = [stream for stream in streams if
                          stream.id not in {stream.id for stream in unauthorized_streams}]
    return authorized_streams, unauthorized_streams

def list_to_streams(streams_raw: Iterable[Mapping[str, Any]],
                    user_profile: UserProfile,
                    autocreate: bool=False) -> Tuple[List[Stream], List[Stream]]:
    """Converts list of dicts to a list of Streams, validating input in the process

    For each stream name, we validate it to ensure it meets our
    requirements for a proper stream name using check_stream_name.

    This function in autocreate mode should be atomic: either an exception will be raised
    during a precheck, or all the streams specified will have been created if applicable.

    @param streams_raw The list of stream dictionaries to process;
      names should already be stripped of whitespace by the caller.
    @param user_profile The user for whom we are retrieving the streams
    @param autocreate Whether we should create streams if they don't already exist
    """
    # Validate all streams, getting extant ones, then get-or-creating the rest.

    stream_set = {stream_dict["name"] for stream_dict in streams_raw}

    for stream_name in stream_set:
        # Stream names should already have been stripped by the
        # caller, but it makes sense to verify anyway.
        assert stream_name == stream_name.strip()
        check_stream_name(stream_name)

    existing_streams: List[Stream] = []
    missing_stream_dicts: List[Mapping[str, Any]] = []
    existing_stream_map = bulk_get_streams(user_profile.realm, stream_set)

    for stream_dict in streams_raw:
        stream_name = stream_dict["name"]
        stream = existing_stream_map.get(stream_name.lower())
        if stream is None:
            missing_stream_dicts.append(stream_dict)
        else:
            existing_streams.append(stream)

    if len(missing_stream_dicts) == 0:
        # This is the happy path for callers who expected all of these
        # streams to exist already.
        created_streams: List[Stream] = []
    else:
        # autocreate=True path starts here
        if not user_profile.can_create_streams():
            raise JsonableError(_('User cannot create streams.'))
        elif not autocreate:
            raise JsonableError(_("Stream(s) (%s) do not exist") % ", ".join(
                stream_dict["name"] for stream_dict in missing_stream_dicts))

        # We already filtered out existing streams, so dup_streams
        # will normally be an empty list below, but we protect against somebody
        # else racing to create the same stream.  (This is not an entirely
        # paranoid approach, since often on Zulip two people will discuss
        # creating a new stream, and both people eagerly do it.)
        created_streams, dup_streams = create_streams_if_needed(realm=user_profile.realm,
                                                                stream_dicts=missing_stream_dicts)
        existing_streams += dup_streams

    return existing_streams, created_streams

def access_default_stream_group_by_id(realm: Realm, group_id: int) -> DefaultStreamGroup:
    try:
        return DefaultStreamGroup.objects.get(realm=realm, id=group_id)
    except DefaultStreamGroup.DoesNotExist:
        raise JsonableError(_("Default stream group with id '%s' does not exist.") % (group_id,))

def get_stream_by_narrow_operand_access_unchecked(operand: Union[str, int], realm: Realm) -> Stream:
    """This is required over access_stream_* in certain cases where
    we need the stream data only to prepare a response that user can access
    and not send it out to unauthorized recipients.
    """
    if isinstance(operand, str):
        return get_stream(operand, realm)
    return get_stream_by_id_in_realm(operand, realm)
