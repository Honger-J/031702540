# coding=utf-8
import json
import requests
import re

class SolveAddress:
    def __init__(self, str):
        self.addr = {"姓名": "", "手机": "", "地址": []}
        self.str = str
        self.flg_1 = None
        self.flg_2 = None

    def solve(self):
        ty = int(self.str[0])  # 识别难度
        self.str = self.str[2:-1]  # 删除难度标识 2!、末尾句号
        self.sov_Name()
        self.sov_Phone()

        if ty == 1:
            self.sov_Addr_1()
        elif ty == 2:
            self.sov_Addr_2()
        else:
            self.sov_Addr_3()

        self.addr = json.dumps(self.addr, ensure_ascii=False)
        print(self.addr)

    def sov_Name(self):
        self.addr["姓名"] = self.str.split(",")[0]
        self.str = self.str.split(",")[1]

    def sov_Phone(self):
        self.addr["手机"] = re.search("\d{11}", self.str).group()  # 识别手机号
        # 除去手机号后地址拼接
        start = re.search("\d{11}", self.str).span()[0]  # 手机号位置起始
        self.str = self.str[:start] + self.str[start + 11:]

    def sov_Addr_1(self):
        # 省级
        if re.match("北京|天津|上海|重庆", self.str) != None:  # 直辖市
            s = re.search("北京市|天津市|上海市|重庆市|北京|天津|上海|重庆", self.str)[0]
            self.addr["地址"].append(s[:2])
            # 直辖市部分切割出去
            self.str = self.str[2:]
            if self.str[0] == "市":
                self.str = self.str[1:]

            url = "https://restapi.amap.com/v3/config/district?key=c80c6911234bd35e6c15fd7b0d0e415a&keywords=" + s + "&subdistrict=3&extensions=base"
            map = requests.get(url).json()["districts"]  # 高德API

        elif re.search("自治区|特别行政区", self.str) != None:
            end = re.search("自治区|特别行政区", self.str).span()[1]
            s = self.str[:end]
            self.addr["地址"].append(s)
            self.str = self.str[end:]  # str省级部分分离出去

            url = "https://restapi.amap.com/v3/config/district?key=c80c6911234bd35e6c15fd7b0d0e415a&keywords=" + s + "&subdistrict=3&extensions=base"
            map = requests.get(url).json()["districts"]  # 高德API
            map = map[0]["districts"]  # 往下移一级

        else:  # 有 省 后缀的， 取前两个字匹配
            s = self.str[:2]
            url = "https://restapi.amap.com/v3/config/district?key=c80c6911234bd35e6c15fd7b0d0e415a&keywords=" + s + "&subdistrict=3&extensions=base"
            map = requests.get(url).json()["districts"]  # 高德API

            ss = map[0]["name"]
            self.addr["地址"].append(ss)
            map = map[0]["districts"]
            # 删除str省级
            self.str = self.str[len(ss) - 1:]  # str省级部分分离出去
            if self.str[0] == "省":
                self.str = self.str[1:]

        # 市级
        # 直辖市
        if self.addr["地址"][0] == "北京" or self.addr["地址"][0] == "上海" or self.addr["地址"][0] == "天津" or self.addr["地址"][
            0] == "重庆":
            self.addr['地址'].append(self.addr["地址"][0] + "市")
            map = map[0]["districts"][0]["districts"]

        else:  # 一般市，市级末尾可能不是市，市字缺失
            s = self.str[:2]
            for i in map:
                if re.match(s, i["name"]) != None:
                    self.addr["地址"].append(i["name"])  # '市'字缺失不用补
                    # str切割市级部分
                    if i["name"][-1] == "市":
                        self.str = self.str[len(i["name"]) - 1:]
                        if self.str[0] == "市":  # '市'字缺失
                            self.str = self.str[1:]
                    else:
                        self.str = self.str[len(i["name"]):]
                    break
            if re.match(s, i["name"]) == None:  # 整个市缺失
                self.addr["地址"].append("")
            else:
                map = i["districts"]

        # 县级
        s = self.str[:2]
        if self.addr["地址"][1] == "":  # 整个市级缺失
            j = None
            for i in map:
                for j in i["districts"]:
                    if re.search(s, j["name"]) != None:
                        self.addr["地址"].append(j["name"])
                        break
                    map = j["districts"]
                if re.search(s, j["name"]) != None:  # 报错
                    break
            self.str = self.str[len(j["name"]):]
            map = j["districts"]
            self.flg_1 = i["name"]  # 难度3用

        else:
            for i in map:
                if re.match(s, i["name"]) != None:  # 匹配到
                    self.addr["地址"].append(i["name"])
                    # str切割县级部分
                    self.str = self.str[len(i["name"]):]
                    break
            if re.match(s, i["name"]) == None:  # 整个县缺失
                self.addr["地址"].append("")
            else:
                map = i["districts"]

        # 乡级
        s = self.str[:2]
        if self.addr["地址"][2] == "":  # 整个县级缺失
            j = None
            for i in map:
                for j in i["districts"]:
                    if re.search(s, j["name"]) != None:
                        self.addr["地址"].append(j["name"])
                        map = j["districts"]
                        break
                if re.search(s, j["name"]) != None:
                    break
            self.str = self.str[len(j["name"]):]
            map = j["districts"]
            self.flg_2 = i["name"]  # 难度3用

        else:
            for i in map:
                if re.match(s, i["name"]) != None:  # 匹配到
                    self.addr["地址"].append(i["name"])
                    # str切割乡级部分
                    self.str = self.str[len(i["name"]):]
                    break
            if re.match(s, i["name"]) == None:  # 整个乡缺失
                self.addr["地址"].append("")
            map = i["districts"]

        # 第五级
        self.addr["地址"].append(self.str)

    def sov_Addr_2(self):
        self.sov_Addr_1()
        self.addr["地址"].pop()
        # 第5级---路、街、巷、村、道、区
        if re.search("路|道|街|巷|村|区", self.str) == None:
            self.addr["地址"].append("")
        else:
            end = re.search("路|道|街|巷|村|区", self.str).span()[1]
            self.addr["地址"].append(self.str[:end])
            self.str = self.str[end:]

        # 第六级---门牌号
        if re.search("号", self.str) == None:
            self.addr["地址"].append("")
        else:
            end = re.search("号", self.str).span()[1]
            self.addr["地址"].append(self.str[:end])
            self.str = self.str[end:]

        # 第七级
        if self.str == None:
            self.addr["地址"].append("")
        else:
            self.addr["地址"].append(self.str)

    def sov_Addr_3(self):
        self.sov_Addr_2()
        if self.addr["地址"][1] == "":
            self.addr["地址"][1] = self.flg_1
        elif self.addr["地址"][2] == "":
            self.addr["地址"][2] = self.flg_2
            
string = input()
solve = SolveAddress(string)
solve.solve()
