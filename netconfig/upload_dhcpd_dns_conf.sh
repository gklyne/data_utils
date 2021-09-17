# upload_dhcpd_dns_conf.sh
#
# Upload specified DHCP and DNS host information files to Luggage server

# SCP = scp -i ~/.ssh/id_rsa_luggage_gk-admin ....
# DATEPREFIX = $(date "+%Y%m%d")

scp -i ~/.ssh/id_rsa_luggage_gk-admin atuin.ninebynine.org.dhcpd.conf gk-admin@luggage.atuin.ninebynine.org:

scp -i ~/.ssh/id_rsa_luggage_gk-admin atuin.ninebynine.org.zone.hosts gk-admin@luggage.atuin.ninebynine.org:

