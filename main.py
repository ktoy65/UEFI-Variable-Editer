import os
import sys
import ctypes
current_dir = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":sys.path.append(current_dir)
from common import *
import bios_parse
import setup_var
from shutil import get_terminal_size
import boot_set
set_auto_boot = True
cur_title = None

if __name__ == "__main__":
    columns, rows = get_terminal_size()
    print("\n" * rows)
    
    if is_admin():
        print("已在管理员权限下运行\n")
    else:
        print("已在用户权限下运行\n")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
        exit(1)


    print("本程序用于一站完成ru修改uefi变量\n"
          "为完成目的需要涉及到修改启动项，此功能可以在程序内关闭，作为代替，请手动在运行后将文件夹下EFI文件夹复制到fat32分区自行引导\n\n"
          ">使用方式：\n"
          "回复菜单序号以进行下一步操作,首先通过搜寻选项找到要改的值（菜单或搜索变量）,随后保存&写入引导生成引导文件\n\n"
          ">自动引导："
          "\n自动配置引导会在 保存&写入引导 时将脚本修改到主机引导首位,并在重启时启动脚本，脚本运行后自动删除自身引导使系统引导回到首位\n"
          "！！注意！！\n自动引导需要一个已经挂载的Fat32分区10M左右空间以放置引导，请提前挂载！！\n"
          "！！注意！！\n程序暂未添加检测引导选项，如果使用自动配置引导，请勿多次保存配置，这将会导致添加多个引导选项，请重启配置完后再保存。\n")
    print("MADE BY 不锈钢电热水壶")
    os.system("pause")

    arg = input("是否跳过BIOS DUMP？(y/n 默认：n）")
    if arg == 'y' or arg == 'Y' or arg == 'yes' or arg == 'Yes' or arg == 'YES':
        bios_parse.init(True, False)
    else:
        bios_parse.init(False,True)

    setup_var.load_json()

    columns, rows = get_terminal_size()
    print("\n" * rows)

    while True:
        if setup_var.add_options_list_final_code:
            print("修改缓存列表：")
            j = 0
            for i in setup_var.add_options_list:
                j +=1
                print(f"{j}: {i[0]} ---> {int(i[1])}")
            print("\n")
        if cur_title is not None:
            print(f"当前指定菜单：{cur_title[1]}\n")

        tmp_str = ""
        tmp_str2 = ""
        if set_auto_boot:
            tmp_str = "关闭"
            tmp_str2 = "3. 写入引导（请勿多次写入，如多次写入请使用文件夹下boot.exe删除多余启动项目)"
        else:
            tmp_str = "开启"
            tmp_str2 = "3. 保存为EFI文件夹（只保存脚本文件夹 .EFI)"


        arg = input(f"1. 通过变量名称查找选项\n2. 通过菜单名称查找选项\n{tmp_str2}\n4. {tmp_str}自动引导\n5. 删除暂存项目\n6. 重启\n>")
        if arg == '1':
            name = input("名称：>")
            result = setup_var.search_offset_name(name)
            if not result:
                columns, rows = get_terminal_size()
                print("\n" * rows)
                print("没有此项")
                continue
            setup_var.print_offset_list(result)
            which = input("哪一个：>")

            if (which == "") or int(which) > len(result) or int(which) <= 0:
                columns, rows = get_terminal_size()
                print("\n" * rows)
                print("无效选择")
                continue

            value = input("改多少：>")
            if (value == "") or not setup_var.add_var_setting(result[int(which)-1], int(value)):
                columns, rows = get_terminal_size()
                print("\n" * rows)
                print("值不符合要求")
                continue

        elif arg == '2':
            re_choose = False
            if cur_title is not None:
                result = setup_var.search_offset_name_by_title_index(cur_title[2])
                setup_var.print_offset_list(result)
                print("0:重新寻找一个列表...")

                which = input("哪一个：>")
                if (which == "") or int(which) > len(result) or int(which) < 0:
                    columns, rows = get_terminal_size()
                    print("\n" * rows)
                    print("无效选择")
                    continue

                if int(which) == 0:
                    re_choose = True
                else:
                    value = input("改多少:>")
                    if (value == "") or not setup_var.add_var_setting(result[int(which) - 1], int(value)):
                        columns, rows = get_terminal_size()
                        print("\n" * rows)
                        print("值不符合要求")
                        continue

            if (cur_title is None) or re_choose:
                t_name = input("菜单名：>")
                result = setup_var.search_offset_title(t_name)
                if result:
                    setup_var.print_title_list(result)
                else:
                    columns, rows = get_terminal_size()
                    print("\n" * rows)
                    print("没有搜到...今日无事可做...")
                    continue


                title = input("第几个：>")
                if (title == "") or int(title) > len(result) or int(title) < 0:
                    columns, rows = get_terminal_size()
                    print("\n" * rows)
                    print("数目不符合要求")
                    continue

                cur_title = result[int(title)-1]


        elif arg == '3':
            if not setup_var.add_options_list_final_code:
                columns, rows = get_terminal_size()
                print("\n" * rows)
                print("没有缓存的选项可保存...今日无事可做...")
                continue
            if set_auto_boot:
                result = boot_set.save_and_set_boot()
                if not result[0]:
                    columns, rows = get_terminal_size()
                    print("\n" * rows)
                    if result[1] == "nodisk":
                        print("没有找到合适的引导设备，请先挂载一个fat32/efi分区")
                        continue
                    else:
                        print(result[1])
                        continue
            else:
                boot_set.save_and_only_create_boot_dir()


        elif arg == '4':
            if set_auto_boot:
                set_auto_boot = False
            else:
                set_auto_boot = True

        elif arg == '5':
            if not setup_var.add_options_list_final_code:
                columns, rows = get_terminal_size()
                print("\n" * rows)
                print("没有缓存的选项...今日无事可做...")
                continue
            which = input("哪一个:>")
            if (which == "") or int(which) > len(setup_var.add_options_list_final_code) or int(which) <= 0:
                columns, rows = get_terminal_size()
                print("\n" * rows)
                print("无效选择")
                continue
            setup_var.rm_var_setting(int(which)-1)

        elif arg == '6':
            result = input("确定要重启吗？(y/n 默认y)")
            if result == 'n'or result == 'N'or result == 'no'or result == 'NO'or result == 'No':
                columns, rows = get_terminal_size()
                print("\n" * rows)
                print("今日无事可做...")
                continue
            os.system("shutdown /r /t 0")

        else:
            columns, rows = get_terminal_size()
            print("\n" * rows)
            print("看不懂...")
            continue



        columns, rows = get_terminal_size()
        print("\n" * rows)
        print("成功")