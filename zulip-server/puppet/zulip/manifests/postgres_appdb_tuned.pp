# postgres_appdb_tuned extends postgres_appdb_base by automatically
# generating tuned database configuration.
class zulip::postgres_appdb_tuned {
  include zulip::postgres_appdb_base

  $work_mem = $zulip::base::total_memory_mb / 512
  $shared_buffers = $zulip::base::total_memory_mb / 8
  $effective_cache_size = $zulip::base::total_memory_mb * 10 / 32
  $maintenance_work_mem = $zulip::base::total_memory_mb / 32

  $random_page_cost = zulipconf('postgresql', 'random_page_cost', undef)
  $effective_io_concurrency = zulipconf('postgresql', 'effective_io_concurrency', undef)
  $replication = zulipconf('postgresql', 'replication', undef)
  $listen_addresses = zulipconf('postgresql', 'listen_addresses', undef)

  $ssl_cert_file = zulipconf('postgresql', 'ssl_cert_file', undef)
  $ssl_key_file = zulipconf('postgresql', 'ssl_key_file', undef)
  $ssl_ca_file = zulipconf('postgresql', 'ssl_ca_file', undef)

  file { $zulip::postgres_appdb_base::postgres_confdirs:
    ensure => directory,
    owner  => 'postgres',
    group  => 'postgres',
  }

  $postgres_conf_file = "${zulip::postgres_appdb_base::postgres_confdir}/postgresql.conf"
  file { $postgres_conf_file:
    ensure  => file,
    require => Package[$zulip::postgres_appdb_base::postgresql],
    owner   => 'postgres',
    group   => 'postgres',
    mode    => '0644',
    content => template("zulip/postgresql/${zulip::base::postgres_version}/postgresql.conf.template.erb"),
  }

  exec { $zulip::postgres_appdb_base::postgres_restart:
    require     => Package[$zulip::postgres_appdb_base::postgresql],
    refreshonly => true,
    subscribe   => [ File[$postgres_conf_file] ]
  }
}
