import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
if __name__ == "__main__":sys.path.append(current_dir)
from common import *
import re
import uefi_firmware
import shutil

uefi_variable_file_content = None
var_store_list = None

def get_Me_Version():
    '''
    此函数运行pnputil指令并匹配返回值拿取me的版本
    :return: 返回四节版本号元组
    '''

    # 构建指令
    command = ['pnputil', '/enum-devices','/properties']
    output = run_command(command)
    print 

    # 匹配Intel(R) Management Engine Interface 区块及其信息
    rstr_get_me_device = r"(ID:(?:(?!\n\n).)*?Intel\(R\) Management Engine Interface(?:(?!\n\n).)*?)(?=\n\n|$)"
    pattern = re.compile(rstr_get_me_device,re.S)
    match = re.findall(pattern,output)
    if not match:
        print("未能获取ME版本-1")
        return None

    # 匹配me版本号
    rstr_get_me_version = r"DEVPKEY_Device_FirmwareVersion.*?\n\s+([0-9]+)\.([0-9]+)\.([0-9]+)\.([0-9]+).*\n"
    pattern = re.compile(rstr_get_me_version,re.S)
    version =  re.findall(pattern,match[0])
    if not version:
        #print(version[0])
        print("未能获取ME版本-2")
        return None

    #返回四节版本号元组
    return version[0]

def dumpBios():
    '''
    使用合适的csme tools提取bios rom
    :return: -
    '''

    #匹配版本号
    version = get_Me_Version()
    if not version:
        print("终止bios提取...")
        print(f"如果不希望通过本程序自动提取bios，请将bios提取文件放置于根目录并保存为dump.bin")
        os.system("pause")
        return
    print(f"Intel ME 版本: {version[0]}.{version[1]}")
    restr_get_dir = r".*v"+version[0]+r"\."+version[1]+r".*"


    #提取dump.bin
    for dir in os.listdir(r".\dumpTools"):
        match = re.search(restr_get_dir, dir)
        if match:
            print(f"找到对应版本的提取工具: {match.group()}")
            print("开始提取 ...")
            for r,d,f, in os.walk(os.path.join(r'dumpTools', dir)):
                for file in f:
                    if file == "FPTW64.exe":
                        output = run_command([os.path.join(current_dir,r , file),"-bios","-d",os.path.join(current_dir,"dump.bin")])
            print("提取完成 ...")
        else:
            print(f"未能找到对应版本的提取工具 v{version[0]}.{version[1]},请在网站自行下载工具解压放在dumpTools文件夹下,并保证文件夹有 v{version[0]}.{version[1]} 字符串\n")
            print("https://comsystem-tlt.ru/obzori/me-txe-region     Intel CSME System Tools xx.x")
            print(f"如果不希望通过本程序自动提取bios，请将bios提取文件放置于根目录并保存为dump.bin")
            os.system("pause")

def dump_and_parse_bios(skip = True,redo = False):
    if skip:
        pass
    else:
        #查找已有bin，用于跳过dump
        if os.path.isfile(os.path.join(current_dir,"dump.bin")):
            print("找到已存在的dump.bin")
            if redo:
                print("进行重新提取...")
                os.remove(os.path.join(current_dir,"dump.bin"))
                dumpBios()
                if not os.path.isfile(os.path.join(current_dir, "dump.bin")):
                    print("提取失败..未找到dump.bin")
                    exit(1)
        else:
            dumpBios()
            if not os.path.isfile(os.path.join(current_dir, "dump.bin")):
                print("提取失败..未找到dump.bin")
                exit(1)


        # 解析bios-----引用自项目
        check_and_create_directory("bios")
        with open('dump.bin', 'rb') as fh:
            file_content = fh.read()
        parser = uefi_firmware.AutoParser(file_content)
        if parser.type() != 'unknown':
            firmware = parser.parse()
            #firmware.showinfo()
            firmware.dump("bios")

        # 找到bios地址文件
        list_result_files = []#存储可能的匹配对象
        bstr_pattern = b'\x53\x00\x65\x00\x74\x00\x75\x00\x70\x00\x00\x00'# setup
        restr_file_ui = r".*\.ui"
        for r,d,f in os.walk("bios"):
            for file in f:
                if re.match(restr_file_ui, file):
                    dirfile =os.path.join(r,file)
                    file_content = read_file(dirfile)
                    if file_content and (bstr_pattern == file_content):
                        list_result_files.append(dirfile)

        # 解析bios
        copy_file(os.path.join(current_dir,os.path.join(os.path.dirname(list_result_files[0]),"section2.pe")),os.path.join(current_dir,"parseData"))
        out = run_command([r"parseData\ifrextractor.exe",os.path.join(current_dir,"parseData","section2.pe")])
        print(out)
        shutil.rmtree(os.path.join(current_dir,"bios"))

def regx_intel_advance_menu():
    # 获取寻找指定的bios文件
    restr_file = r"FormSet\sGuid:\s[0-9A-F\-]*,\sTitle:\s\"Intel\sAdvanced\sMenu\","
    # 查找bios对应文件
    for r, d, f in os.walk("parseData"):
        restr_txt = r".*\.txt$"
        for file in f:
            if re.search(restr_txt, file):  # 检查是否是txt
                temp = read_file(os.path.join(r, file), "r")
                if re.search(restr_file, temp):  # 检查是否符合要求
                    return os.path.join(r,file)

def regx_var_store_info(content):
    """
    拿取所有varStore信息
    :return: varstore 信息 list
    """
    restr_Get_Var_Store_info = r"Guid:\s([0-9A-F\-]*),\sVarStoreId:\s([0-9A-Fx]+).*,\sSize:\s([0-9A-Fx]+),\sName:\s\"([\S]+)\"\n"
    pattern_ = re.compile(restr_Get_Var_Store_info,re.IGNORECASE)
    var_store_list_ = []
    for i in content:
        tmp=re.findall(pattern_, i)
        if tmp:
            var_store_list_.append(tmp[0])
    return var_store_list_

def regx_titles_info(content):
    #匹配菜单
    t_list = []
    restr_title = r"Form\sFormId:\s[A-F0-9x]*,\sTitle:\s\"([^\"]+)\""
    pattern_ = re.compile(restr_title,re.IGNORECASE)
    for i in range(len(content)):
        tmp = re.findall(pattern_, content[i])
        if tmp:
            offset_base_list = [i, tmp[0]]
            t_list.append(offset_base_list)
    return t_list

def regx_offset_info(content,search,type="name",titles_list_=None)->list:
    if not titles_list_:
        titles_list_ = regx_titles_info(content)

    offset_list_ = []
    if type=="name":
        #匹配选项变量
        search_name = search
        if search_name =='':
            search_name = r".+"
        else:
            search_name = search_name.replace(" ",r"\s")

        #匹配符----选择offset值
        reg1 = r"([\S]+)\sPrompt:\s\"([^\"]*"
        reg2 = r"[^\"]*)\",\sHelp:\s\"([^\"]*)\",[^\n]*,\sVarStoreId:\s([0-9A-Fx]+),\sVarOffset:\s([0-9A-Fx]+).*,\sSize:\s([0-9A-Fx]+),\sMin:\s([0-9A-Fx]+),\sMax:\s([0-9A-Fx]+)"
        regx = reg1+search_name+reg2
        pattern = re.compile(regx,re.IGNORECASE)

        #匹配offset值
        title_line_index = 0
        for i in range(len(content)):
            title_name = ''
            tmp = re.findall(pattern, content[i])
            if tmp:#去除空白选项
                for j in range(title_line_index,len(titles_list_)): #将菜单名称与选项进行匹配，j为检测到的title所在列表的index
                    if titles_list_[j][0] > i: #如果title所在行数大于了匹配选项的行数，就将匹配选项分配给上一个title，同时记录j的值，下次直接从j-1开始判定
                        title_line_index = j-1
                        title_name = titles_list_[j-1][1]
                        break
                tmp = list(tmp[0])#去除元组
                tmp.insert(0, title_name)#将菜单名插入首位
                offset_list_.append(tmp)#添加结果

        return offset_list_
    elif type=="menu":
        reg1 = r"([\S]+)\sPrompt:\s\"([^\"]*"
        reg2 = r"[^\"]*)\",\sHelp:\s\"([^\"]*)\",[^\n]*,\sVarStoreId:\s([0-9A-Fx]+),\sVarOffset:\s([0-9A-Fx]+).*,\sSize:\s([0-9A-Fx]+),\sMin:\s([0-9A-Fx]+),\sMax:\s([0-9A-Fx]+)"
        regx = reg1+reg2
        pattern = re.compile(regx, re.IGNORECASE)

        for i in range(titles_list_[search][0],titles_list_[search+1][0]):
            tmp = re.findall(pattern, content[i])
            if tmp:
                tmp = list(tmp[0])
                tmp.insert(0, titles_list_[search][1])
                offset_list_.append(tmp)
        return offset_list_

def get_var_store_name(hex_code):
    hex_set = hex_code
    if type(hex_set) == str:
        for i in var_store_list:
            if i[1] == hex_set:
                return i[3]
    elif type(hex_set) == int:
        for i in var_store_list:
            if i[1] == hex(hex_set):
                return i[3]

def search_title(name):
    restr_title_name = r"[\S]*"+name+r"[\S]*"
    pattern = re.compile(restr_title_name,re.IGNORECASE)
    result_list = []
    j = 0
    for i in regx_titles_info(uefi_variable_file_content):
        j+=1
        tmp = re.findall(pattern, i[1])
        if tmp:
            tmp = i +[j-1] # 去除元组
            result_list.append(tmp)
    # 添加结果
    return result_list



#init
#dump bios 固件
def init(skip = True,redo = False):
    global var_store_list
    global uefi_variable_file_content
    dump_and_parse_bios(skip,redo)

    if not regx_intel_advance_menu():
        print("找不到可以分析的解包文件...程序将终止")
        print("如需自行解包，请将由parseData\ifrextractor.exe文件解包的setup变量表文件放在parseData文件夹下")
        os.system("pause")
        exit(1)
    uefi_variable_file_content = read_file_lines(regx_intel_advance_menu(),"r")
    var_store_list = regx_var_store_info(uefi_variable_file_content)




if __name__ == "__main__":
    if is_admin():
        print("You are running as an administrator.")
        # 在这里执行需要管理员权限的操作
    else:
        exit()
    #dump bios 固件
    dump_and_parse_bios(skip = False,redo=True)
    # #读取文件内容变量
    # uefi_variable_file_content =  read_file_lines(regx_intel_advance_menu(),"r")
    # #匹配uefi变量地址
    # var_store_list = regx_var_store_info(uefi_variable_file_content)
    # #匹配offset变量
    # offset_list = regx_offset_info(uefi_variable_file_content,"")
    #
    # for i in offset_list:
    #     print(i)












