from django.db import models

class Entry(models.Model):
  username = models.CharField('username', max_length=32)
  ip = models.CharField('IP address', max_length=45)
  port = models.PositiveIntegerField('port')
  mitm_ip = models.CharField('MITM IP address', max_length=45, blank=True)
  mitm_port = models.PositiveIntegerField('MITM Port', blank=True)
  core_name = models.CharField('core name', max_length=200)
  core_version = models.CharField('core version', max_length=200)
  game_name = models.CharField('game name', max_length=200)
  game_crc = models.CharField('game CRC', max_length=200)
  fixed = models.BooleanField('fixed', default=False)
  has_password = models.BooleanField('has password', default=False)

  HOST_CHOICES = (
    (0, 'Unknown'),
    (1, 'Manual'),
    (2, 'UPNP'),
    (3, 'MITM'),
  )

  host_method = models.PositiveSmallIntegerField('host method', choices=HOST_CHOICES)
  created = models.DateTimeField('created', auto_now_add=True)
  updated = models.DateTimeField('updated', auto_now=True)

  def __unicode__(self):
    return self.username + '@' + self.ip + ' Core: ' + self.core_name + ' ' + self.core_version + ' Game: ' + self.game_name

  class Meta:
    verbose_name_plural = 'Entries'
