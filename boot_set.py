import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":sys.path.append(current_dir)
import wmi
import common
import setup_var

bootice = r"BOOT.exe"
boot_tools = r"bootTools"
boot_efi = r"uefi_shell.efi"

reset_boot_nsh = "bcfg boot rm 0\n"
goto_working_dir_nsh = '''for %p in fs0 fs1 fs2 fs3 fs4 fs5 fs6 fs7 fs8 fs9
  if exist %p:\\bootTools\\setup_var.efi then
    echo find: %p
    %p:
    cd bootTools
    goto SETVAR
  endif
endfor

:SETVAR
'''
goto_working_dir_nsh_standard = '''for %p in fs0 fs1 fs2 fs3 fs4 fs5 fs6 fs7 fs8 fs9
  if exist %p:\\EFI\\Boot\\setup_var.efi then
    echo find: %p
    %p:
    cd \\EFI\\Boot
    goto SETVAR
  endif
endfor

:SETVAR
'''

def get_boot_disk():
    c = wmi.WMI()

    # 获取所有逻辑磁盘
    logical_disks = c.Win32_LogicalDisk()

    efi_disks_list = []
    # 遍历所有逻辑磁盘
    for disk in logical_disks:
        if disk.FileSystem in ["FAT32", "FAT", "FAT16"]:
            efi_disks_list.append(disk.Caption)
            #print(f"盘符: {disk.Caption}, 卷标: {disk.VolumeName},GUID: {disk.DeviceID}")
    return efi_disks_list

def get_disk_guid(disk_volume_signal):
    c = wmi.WMI(namespace='root\\Microsoft\\Windows\\Storage')

    # 获取所有分区
    partitions = c.MSFT_Partition()

    efi_disks_list = []
    # 遍历所有分区
    for partition in partitions:
        efi_disks_list.append(partition)

    # 打印信息
    for part in efi_disks_list:
        disk = disk_volume_signal + "\\"
        if part.AccessPaths:
            if disk == part.AccessPaths[0]:
                print(f"盘符: {part.AccessPaths}, GUID: {part.Guid}, 大小: {part.Size}")
                return part.Guid

    #print("所有EFI分区已列出。")

def cp_boot_tools_to_disk(target):
    common.check_and_create_directory(os.path.join(target, boot_tools))
    for r,d,f in os.walk(boot_tools):
        for file in f:
            result = common.copy_file(os.path.join(r,file), os.path.join(target,boot_tools,file))
            if not result[0]:
                return result
    return (True,None)

def add_boot_sequence(file):
    print([bootice,"/uefi","/add","/inspos=0","file=\""+file+"\"","/title=\"varsetup\""])
    os.system(f"boot.exe /uefi /add /inspos=0 /file=\"{file}\" /title=\"varsetup\"")

def rewrite_nsh(vars_content,enable_auto_boot = True):
    code = ""
    if enable_auto_boot:
        code += reset_boot_nsh
        code +='\n'
    code += goto_working_dir_nsh
    code += '\n'
    code += vars_content
    common.write_file(os.path.join(current_dir,"bootTools","startup.nsh"),code,'w')

def save_and_set_boot():
    auto_boot = True
    disk = get_boot_disk()[0]
    if not disk:
        return False, "nodisk"

    disk = disk + "\\"
    rewrite_nsh(setup_var.gen_file_content(auto_boot),auto_boot)
    result = cp_boot_tools_to_disk(disk)
    if not result[0]:
        return False,result[1]

    add_boot_sequence(os.path.join(disk,boot_tools,boot_efi))
    return True,None

def save_and_only_create_boot_dir():
    rewrite_nsh(setup_var.gen_file_content(False), False)
    common.check_and_create_directory(os.path.join(current_dir, "EFI"))
    common.check_and_create_directory(os.path.join(current_dir, "EFI", "Boot"))
    for r,d,f in os.walk(boot_tools):
        for file in f:
            if file == boot_efi:
                common.copy_file(os.path.join(r, file), os.path.join(os.path.join(current_dir, "EFI", "Boot"), "bootx64.efi"))
            else:
                common.copy_file(os.path.join(r,file), os.path.join(os.path.join(current_dir, "EFI", "Boot"),file))



if __name__ == "__main__":
    pass

