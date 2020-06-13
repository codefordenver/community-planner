# Zulip server release checklist

This document has reminders of things one might forget to do when
preparing a new release.

### A week before the release

* Upgrade all Python dependencies in `requirements` to latest
  upstream versions so they can burn in (use `pip list --outdated`).
* Update all the strings on Transifex and notify translators that they
  should translate the new strings to get them in for the next
  release.
* Update `changelog.md` with major changes going into the release.
* Create a burndown list of bugs that need to be fixed before we can
  release, and make sure all of them are being worked on.
* Draft the release blog post (aka the release notes.)

### Final release preparation

* Update `changelog.md` with any changes since the last update, and
  with revisions from the draft blog post.
* Download updated translation strings from Transifex and commit them.
* Use `build-release-tarball` to generate a release tarball.
* Test the new tarball extensively, both new install and upgrade from last
  release, on both Bionic and Focal.
* Repeat until release is ready.
* When near finished: move the blog post draft to Ghost.  (For a draft
  in Dropbox Paper, use "··· > Download > Markdown" to get a pretty
  good markup conversion.)  Proofread the post, especially for
  formatting.

### Executing the release

* Do final updates to `changelog.md`, for any final changes and with
  any revisions from the draft blog post.  (And the date!)
* Update `ZULIP_VERSION` and `LATEST_RELEASE_VERSION` in `version.py`.
* Use `build-release-tarball` to generate a final release tarball.
* Post the release tarball on https://www.zulip.org/dist/releases/ :
  add the file, update the `zulip-server-latest.tar.gz` symlink, and
  add to SHA256SUMS.txt, using `ship-release.sh`.
* Create a Git tag and push the tag.
* Post the release on GitHub, using the text from `changelog.md`.
* Update the [Docker image](https://github.com/zulip/docker-zulip) and do a release of that.
* Update the image of DigitalOcean one click app using [Fabric](https://github.com/zulip/marketplace-partners)
  and publish it to DO marketplace.
* Publish the blog post.
* Email zulip-announce, post to #announce, and send a tweet.

### Post-release

* Push the release commit to master, if applicable (typically for a
  major release); otherwise, make sure any last changes make it back
  to master.
* Update `ZULIP_VERSION` in `version.py` to e.g. `2.2.0+git` following
  a 2.1.0 release, and make a Git tag named e.g. `2.2-dev` pointing to
  this update.
* Consider removing a few old releases from ReadTheDocs.
