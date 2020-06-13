# Minimal configuration to run a Zulip application server.
# Default nginx configuration is included in extension app_frontend.pp.
class zulip::app_frontend_base {
  include zulip::common
  include zulip::nginx
  include zulip::sasl_modules
  include zulip::supervisor
  include zulip::tornado_sharding

  if $::osfamily == 'debian' {
    $web_packages = [
      # This is not necessary on CentOS because $postgresql package already includes the client
      # Needed to access our database
      "postgresql-client-${zulip::base::postgres_version}",
      # Needed for Slack import
      'unzip',
    ]
  } else {
      $web_packages = [
        # Needed for Slack import
        'unzip',
      ]
  }
  zulip::safepackage { $web_packages: ensure => 'installed' }

  file { '/etc/nginx/zulip-include/app':
    require => Package[$zulip::common::nginx],
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    source  => 'puppet:///modules/zulip/nginx/zulip-include-frontend/app',
    notify  => Service['nginx'],
  }
  file { '/etc/nginx/zulip-include/uploads.types':
    require => Package[$zulip::common::nginx],
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    source  => 'puppet:///modules/zulip/nginx/zulip-include-frontend/uploads.types',
    notify  => Service['nginx'],
  }
  file { '/etc/nginx/zulip-include/app.d/':
    ensure => directory,
    owner  => 'root',
    group  => 'root',
    mode   => '0755',
  }

  $loadbalancers = split(zulipconf('loadbalancer', 'ips', ''), ',')
  if $loadbalancers != [] {
    file { '/etc/nginx/zulip-include/app.d/accept-loadbalancer.conf':
      require => File['/etc/nginx/zulip-include/app.d'],
      owner   => 'root',
      group   => 'root',
      mode    => '0644',
      content => template('zulip/accept-loadbalancer.conf.template.erb'),
      notify  => Service['nginx'],
    }
  }

  # The number of Tornado processes to run on the server; this
  # defaults to 1, since Tornado sharding is currently only at the
  # Realm level.
  $tornado_processes = Integer(zulipconf('application_server', 'tornado_processes', 1))
  if $tornado_processes > 1 {
    $tornado_ports = range(9800, 9800 + $tornado_processes - 1)
    $tornado_multiprocess = true
  } else {
    $tornado_multiprocess = false
  }

  file { '/etc/nginx/zulip-include/upstreams':
    require => Package[$zulip::common::nginx],
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template('zulip/nginx/upstreams.conf.template.erb'),
    notify  => Service['nginx'],
  }

  # This determines whether we run queue processors multithreaded or
  # multiprocess.  Multiprocess scales much better, but requires more
  # RAM; we just auto-detect based on available system RAM.
  $queues_multiprocess = $zulip::base::total_memory_mb > 3500
  $queues = $zulip::base::normal_queues
  if $queues_multiprocess {
    $uwsgi_default_processes = 6
  } else {
    $uwsgi_default_processes = 4
  }
  file { "${zulip::common::supervisor_conf_dir}/zulip.conf":
    ensure  => file,
    require => Package[supervisor],
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template('zulip/supervisor/zulip.conf.template.erb'),
    notify  => Service[$zulip::common::supervisor_service],
  }

  $uwsgi_listen_backlog_limit = zulipconf('application_server', 'uwsgi_listen_backlog_limit', 128)
  $uwsgi_buffer_size = zulipconf('application_server', 'uwsgi_buffer_size', 8192)
  $uwsgi_processes = zulipconf('application_server', 'uwsgi_processes', $uwsgi_default_processes)
  file { '/etc/zulip/uwsgi.ini':
    ensure  => file,
    require => Package[supervisor],
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template('zulip/uwsgi.ini.template.erb'),
    notify  => Service[$zulip::common::supervisor_service],
  }

  file { '/home/zulip/tornado':
    ensure => directory,
    owner  => 'zulip',
    group  => 'zulip',
    mode   => '0755',
  }
  file { '/home/zulip/logs':
    ensure => 'directory',
    owner  => 'zulip',
    group  => 'zulip',
  }
  file { '/home/zulip/prod-static':
    ensure => 'directory',
    owner  => 'zulip',
    group  => 'zulip',
  }
  file { '/home/zulip/deployments':
    ensure => 'directory',
    owner  => 'zulip',
    group  => 'zulip',
  }
  file { '/srv/zulip-npm-cache':
    ensure => directory,
    owner  => 'zulip',
    group  => 'zulip',
    mode   => '0755',
  }
  file { '/srv/zulip-emoji-cache':
    ensure => directory,
    owner  => 'zulip',
    group  => 'zulip',
    mode   => '0755',
  }
  file { '/etc/cron.d/email-mirror':
    ensure => absent,
  }
  file { "${zulip::common::nagios_plugins_dir}/zulip_app_frontend":
    require => Package[$zulip::common::nagios_plugins],
    recurse => true,
    purge   => true,
    owner   => 'root',
    group   => 'root',
    mode    => '0755',
    source  => 'puppet:///modules/zulip/nagios_plugins/zulip_app_frontend',
  }

  if $::osfamily == 'debian' {
    # The pylibmc wheel looks for SASL plugins in the wrong place.
    file { '/usr/lib64':
      ensure => directory,
    }
    file { '/usr/lib64/sasl2':
      ensure => link,
      target => "/usr/lib/${::rubyplatform}/sasl2",
    }
  }
}
