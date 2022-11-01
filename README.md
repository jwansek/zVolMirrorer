# zVolMirrorer.git

Script for mirroring zVols without using zfs replication

The way you are 'supposed' to backup zVols is to use zfs replication, using `zfs send` and `zfs recv`, but doing it this way has a problem. If, like me, you have a large zVol that uses up most of the space in a given pool, and this zVol contains encrypted data and therefore cannot have incremental backups, then you will not have sufficient space to make a zfs snapshot, and zfs replication only works with zfs snapshots. 

This is a small script that mounts two zVols which are iSCSI targets, then mirrors them using `dd`. This requires making the zVols accessable through iSCSI, and writing a valid iSCSI configuration on the host. It does some checking to make sure that no-one else has mounted the iSCSI shares at the time the backup starts, which requires SSH access through a key to the NAS host.

This method is obviously *much* slower than using ZFS replication but speed is not important for me.

An alternative method would be to make a clonezilla VM on the NAS host, pass through the zVols as disks into the clonezilla VM, and mirror it that way. That'd probably be a lot faster since it doesn't have the iSCSI overhead. However you couldn't easily do this backup as a cronjob. I could'nt do it like this (I blame the rubbish bhyve FreeBSD hypervisor)...
