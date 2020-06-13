# Minimal shared configuration needed to run a Zulip postgres database.
class zulip::postgres_appdb_base {
  include zulip::postgres_common
  include zulip::supervisor
  include zulip::process_fts_updates

  case $::osfamily {
    'debian': {
      include zulip::apt_repository
      $postgresql = "postgresql-${zulip::base::postgres_version}"
      $postgres_sharedir = "/usr/share/postgresql/${zulip::base::postgres_version}"
      $postgres_confdirs = [
        "/etc/postgresql/${zulip::base::postgres_version}",
        "/etc/postgresql/${zulip::base::postgres_version}/main",
      ]
      $postgres_confdir = $postgres_confdirs[-1]
      $postgres_datadir = "/var/lib/postgresql/${zulip::base::postgres_version}/main"
      $tsearch_datadir = "${postgres_sharedir}/tsearch_data"
      $pgroonga_setup_sql_path = "${postgres_sharedir}/pgroonga_setup.sql"
      $setup_system_deps = 'setup_apt_repo'
      $postgres_restart = "pg_ctlcluster ${zulip::base::postgres_version} main restart"
    }
    'redhat': {
      include zulip::yum_repository
      $postgresql = "postgresql${zulip::base::postgres_version}"
      $postgres_sharedir = "/usr/pgsql-${zulip::base::postgres_version}/share"
      $postgres_confdirs = [
        "/var/lib/pgsql/${zulip::base::postgres_version}",
        "/var/lib/pgsql/${zulip::base::postgres_version}/data",
      ]
      $postgres_confdir = $postgres_confdirs[-1]
      $postgres_datadir = "/var/lib/pgsql/${zulip::base::postgres_version}/data"
      $tsearch_datadir = "${postgres_sharedir}/tsearch_data/"
      $pgroonga_setup_sql_path = "${postgres_sharedir}/pgroonga_setup.sql"
      $setup_system_deps = 'setup_yum_repo'
      $postgres_restart = "systemctl restart postgresql-${zulip::base::postgres_version}"
    }
    default: {
      fail('osfamily not supported')
    }
  }

  # We bundle a bunch of other sysctl parameters into 40-postgresql.conf
  file { '/etc/sysctl.d/30-postgresql-shm.conf':
    ensure => absent,
  }

  file { "${tsearch_datadir}/en_us.dict":
    ensure  => 'link',
    require => Package[$postgresql],
    target  => '/var/cache/postgresql/dicts/en_us.dict',  # TODO check cache dir on CentOS
  }
  file { "${tsearch_datadir}/en_us.affix":
    ensure  => 'link',
    require => Package[$postgresql],
    target  => '/var/cache/postgresql/dicts/en_us.affix',  # TODO check cache dir on CentOS

  }
  file { "${tsearch_datadir}/zulip_english.stop":
    ensure  => file,
    require => Package[$postgresql],
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    source  => 'puppet:///modules/zulip/postgresql/zulip_english.stop',
  }
  file { "${zulip::common::nagios_plugins_dir}/zulip_postgres_appdb":
    require => Package[$zulip::common::nagios_plugins],
    recurse => true,
    purge   => true,
    owner   => 'root',
    group   => 'root',
    mode    => '0755',
    source  => 'puppet:///modules/zulip/nagios_plugins/zulip_postgres_appdb',
  }

  $pgroonga = zulipconf('machine', 'pgroonga', '')
  if $pgroonga == 'enabled' {
    # Needed for optional our full text search system
    package{"${postgresql}-pgroonga":
      ensure  => 'installed',
      require => [Package[$postgresql],
                  Exec[$setup_system_deps]],
    }

    file { $pgroonga_setup_sql_path:
      ensure  => file,
      require => Package["${postgresql}-pgroonga"],
      owner   => 'postgres',
      group   => 'postgres',
      mode    => '0640',
      source  => 'puppet:///modules/zulip/postgresql/pgroonga_setup.sql',
    }

    exec{'create_pgroonga_extension':
      require => File[$pgroonga_setup_sql_path],
      # lint:ignore:140chars
      command => "bash -c 'cat ${pgroonga_setup_sql_path} | su postgres -c \"psql -v ON_ERROR_STOP=1 zulip\" && touch ${pgroonga_setup_sql_path}.applied'",
      # lint:endignore
      creates => "${pgroonga_setup_sql_path}.applied",
    }
  }
}
