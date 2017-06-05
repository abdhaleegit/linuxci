#!/bin/bash
cpu=`nproc`
os=`cat /etc/*-release | grep "NAME"`
rm -rf vmlinux
rm -rf initrd-autotest
rm -rf /lib/modules/*-bisect*
echo "Performing Make config"
sed -ie 's/CONFIG_LOCALVERSION=""/CONFIG_LOCALVERSION="-bisect"/g' .config
yes "" | make oldconfig > /dev/null
version=`make kernelrelease |  grep bisect | rev | cut -d" " -f1 | rev`
echo "Performing make install"
make -j$cpu -S vmlinux > /dev/null
if [ $? != 0 ]; then
    exit 2
fi
echo "Performing make modules"
make -j$cpu modules > /dev/null
if [ $? != 0 ]; then
    exit 2
fi
echo "Performing make modules install"
make -j$cpu modules_install > /dev/null
if [ $? != 0 ]; then
    exit 2
fi
# SUSE also initramfs
echo "Creating initrd image"
echo "$os" | grep "Ubuntu"
if [ $? -eq 0 ] 
then
    mkinitramfs -o initrd-autotest $version
    if [ $? != 0 ]; then
        exit 2
    fi
else
    mkinitrd initrd-autotest $version --force
    if [ $? != 0 ]; then
        exit 2
    fi
fi
kexec -l vmlinux --initrd initrd-autotest --append=rw
if [ $? != 0 ]; then
    exit 2
fi
echo "Rebooting . . ."
kexec -e
exit 2
