obj-m += indicator.o
KDIR := /usr/src/linux-headers-$(shell uname -r)

all:
$(MAKE) -C $(KDIR) M=$(PWD) modules
clean:
$(MAKE) -C $(KDIR) M=$(PWD) clean
