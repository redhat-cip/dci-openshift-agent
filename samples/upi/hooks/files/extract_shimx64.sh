#!/usr/bin/sh

echo "copy shimx64.efi,grubx64.efi"
mkdir -p /mnt/iso
mkdir -p /mnt/efiboot
mount -o loop,ro $1 /mnt/iso
mount -o loop,ro /mnt/iso/images/efiboot.img /mnt/efiboot
/bin/cp -f /mnt/efiboot/EFI/redhat/{shimx64.efi,grubx64.efi} $2
umount -l /mnt/efiboot
umount -l /mnt/iso
