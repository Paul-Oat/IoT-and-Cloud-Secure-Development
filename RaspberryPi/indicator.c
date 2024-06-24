
#include "gpioCon.h"
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/fs.h>
#include <linux/uaccess.h>
#include <linux/gpio.h>

static int DevBusy = 0;
static int MajorNum = 100;
static struct class*  ClassName  = NULL;
static struct device* DeviceName = NULL;

lkm_data lkmdata;
gpio_pin apin;


static int device_open(struct inode *inode, struct file *file)
{
        printk(KERN_INFO "piio: device_open(%p)\n", file);

        if (DevBusy)
                return -EBUSY;

        DevBusy++;
        try_module_get(THIS_MODULE);
        return 0;
}

static int device_release(struct inode *inode, struct file *file)
{
        printk(KERN_INFO "piio: device_release(%p)\n", file);
        DevBusy--;

        module_put(THIS_MODULE);
        return 0;
}


static int device_ioctl(struct file *file, unsigned int cmd, unsigned long arg){

        printk("piio: device_ioctl - Device IOCTL invoked : 0x%x - %u\n" , cmd , cmd);

        switch (cmd) {
        case IOCTL_PIIO_GPIO_READ:

                memset(&apin , 0, sizeof(apin));
                copy_from_user(&apin, (gpio_pin *)arg, sizeof(gpio_pin));
                gpio_request(apin.pin, apin.desc);
                apin.value = gpio_get_value(apin.pin);
                strcpy(apin.desc, "LKMpin");
                copy_to_user((void *)arg, &apin, sizeof(gpio_pin));
                printk("piio: IOCTL_PIIO_GPIO_READ - pin:%u - val:%i - desc:%s\n" , apin.pin , apin.value , apin.desc);
                break;

        case IOCTL_PIIO_GPIO_WRITE:
                copy_from_user(&apin, (gpio_pin *)arg, sizeof(gpio_pin));
                gpio_request(apin.pin, apin.desc);
                gpio_direction_output(apin.pin, 0);
                gpio_set_value(apin.pin, apin.value);
                printk("piio: IOCTL_PIIO_GPIO_WRITE - pin:%u - val:%i - desc:%s\n" , apin.pin , apin.value , apin.desc);
                break;
        default:
                        printk("piio: format error\n");
        }

        return 0;
}


struct file_operations Fops = {
        .unlocked_ioctl = (long (*)(struct file *, unsigned int, unsigned long))device_ioctl,
        .open = device_open,
        .release = device_release,
};


static int __init piio_init(void){

           printk(KERN_INFO "piio: initializing the dd\n");
           MajorNum = register_chrdev(0, DEVICE_NAME, &Fops);
              if (MajorNum<0){
                 printk(KERN_ALERT "piio: failed to register with major number\n");
                 return MajorNum;
              }
           printk(KERN_INFO "piio: registered with major number %d\n", MajorNum);


           ClassName = class_create(THIS_MODULE, CLASS_NAME);
           if (IS_ERR(ClassName)){
              unregister_chrdev(MajorNum, DEVICE_NAME);
              printk(KERN_ALERT "piio: failed to register device class\n");
              return PTR_ERR(ClassName);
           }
           printk(KERN_INFO "piio: device class registered\n");


           DeviceName = device_create(ClassName, NULL, MKDEV(MajorNum, 0), NULL, DEVICE_NAME);
           if (IS_ERR(DeviceName)){
              class_destroy(ClassName);
              unregister_chrdev(MajorNum, DEVICE_NAME);
              printk(KERN_ALERT "piio: failed to create the device\n");
              return PTR_ERR(DeviceName);
           }
           printk(KERN_INFO "piio: device class created\n");

