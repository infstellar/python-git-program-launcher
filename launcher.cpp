#include <iostream>
#include <stdio.h>
#include <direct.h>
#include <windows.h>
#include<sys/stat.h>
using namespace std;

HWND hwnd = GetForegroundWindow();  //获取程序启动时的窗口

void HideWindow() {
	if (hwnd) {
		ShowWindow(hwnd, SW_HIDE);	//设置指定窗口的显示状态
	}
}

void ShowWindow() {
	if (hwnd) {
		ShowWindow(hwnd, SW_SHOW);	//设置指定窗口的显示状态
	}
}

bool checkIfFileExists(const char* filename){
    struct stat buffer;
    int exist = stat(filename,&buffer);
    if(exist == 0)
        return true;
    else  
        return false;
}

int main()
{   
    HideWindow();
    // ShowWindow(); // If debug
    char buffer[16384]; 
    getcwd(buffer, 16384);
    string root = buffer;
    string pyBin = root + "\\toolkit";
    string GitBin = root + "\\toolkit\\Git\\mingw64\\bin";
    string env_cmd = "PATH="+pyBin+";"+pyBin+"\\Scripts;"+pyBin+"\\Lib;"+GitBin+";%PATH%";
    cout << env_cmd.c_str() << endl;
    _putenv(env_cmd.c_str());
    char buf[8192]; //缓冲区
    string p_cmd = "cd /d "+root+" && python -m gui";
    cout << p_cmd.c_str() << endl;
    // system(p_cmd.c_str());
    FILE *fp = popen(p_cmd.c_str(),"r");
    if (fp == NULL) //判断管道是否打开成功
    {
        cout << "Fatal Error: Cannot open pipe" << endl;
        ShowWindow();
        return -1;
    }
    int ret = fread(buf, 1, sizeof(buf), fp); //读取显示结果
    if (ret > 0) //判断是否读取成功
    {
        cout << buf << endl; //输出显示结果
        pclose(fp);
        // ShowWindow();
        return 0;
    }
    else
    {
        pclose(fp);
        ShowWindow();
        cout << "Fatal Error: Program Run Failure." << endl;
        cout << "Running automatic error checking..." << endl;
        if (checkIfFileExists((pyBin+"\\python.exe").c_str()) == false){
            cout << "Possible reason: toolkit is not installed. Please check if you downloaded the correct file or if you cloned the submodule." << endl;
        }
        else{
            cout << "No reason founded. Please submit your error message." << endl;
        }
        system("pause");
        return -1;
    }
    ShowWindow();
    return 0;
}
