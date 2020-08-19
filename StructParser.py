import sys
import re
from subprocess import check_output
import subprocess
import os

sys_path = sys.argv[0].replace("StructParser.py", '')
ok_extensions_path = sys_path + "ok_extensions.config"
type_conversion_path = sys_path + "type_conversion.config"

ok_extensions = []
try:
    f_ext = open(ok_extensions_path, 'r')
except:
    print("Error! Cannot read config file:\n" + ok_extensions_path)
    quit()

ok_extensions = list(map(lambda x: x.replace('\n', ''), f_ext.readlines()))
f_ext.close()

type_conversion = {}
try:
    f_conv = open(type_conversion_path, 'r')
except:
    print("Error! Cannot read config file:\n" + type_conversion_path)
    quit()

while True:
    s = f_conv.readline()
    if s == '':
        break
    sa = s.split('--')
    if len(sa) == 3:
        type_conversion[sa[0]] = list(map(lambda x: x.replace('\n', ''), sa[1:]))
    else:
        print("Exception! Type config string cofmat is invalid:\n" + s.replace('\n', '') +
              "\nC_TYPE--JAVA_TYPE--JNI_TYPE expected")
f_conv.close()
files_to_convert = []
i = 0
output_dir = "."
java_dir = "C:\\Program Files\\Java\\jdk-9.0.4"
while i < len(sys.argv):
    p = sys.argv[i]
    if p.startswith('-f') and i < len(sys.argv) - 1:
        if sys.argv[i+1].split('.')[-1].upper() in ok_extensions:
            files_to_convert.append(sys.argv[i+1])
            i += 1
    elif p.startswith('-o') and i < len(sys.argv) - 1:
        output_dir = sys.argv[i+1]
        i += 1
    elif p.startswith('-java') and i < len(sys.argv) - 1:
        java_dir = sys.argv[i+1]
        i += 1
    i += 1

print(files_to_convert)


def parse_struct(text, name, filename):
    print(name)
    jname = name + 'J'
    out_j = open(output_dir + "\\" + jname + '.java', 'w')
    out_j.write('public class ' + jname + ' {\n')
    out_j.write('\tstatic {\n\t\tSystem.load(' +
        'Main.class.getProtectionDomain().getCodeSource().getLocation().getPath().substring(1).replaceAll("/","\\\\\\\\")' +
        ' + "CPP_LIB\\\\\\\\' + jname + '.so");\n\t}\n\n')
    out_j.write('\tprivate long _pointer = 0;\n')
    out_j.write('\tprivate native void init();\n')
    out_j.write('\tprotected native void finalize() throws Throwable;\n')
    out_j.write('\tpublic ' + jname + '() {\n\t\tinit();\n\t}\n')
    out_j.write('\tpublic ' + jname + '(long pointer) {\n\t\t_pointer = pointer;\n\t}\n')

    out_c = open(output_dir + "\\CPP_sources\\" + jname + '.cpp', 'w')
    out_c.write('#ifndef _Included' + jname + '\n#define _Included_' + jname + '\n#include <jni.h>' +
                '\n#include "' + filename + '"\n' +
                '\n#ifdef __cplusplus\nextern "C" {\n#endif\n')
    out_c.write('\nJNIEXPORT void JNICALL Java_' + jname + '_init' +
                '\n(JNIEnv * env, jobject obj) {\n')
    out_c.write('\t' + name + ' * object = new ' + name + '();\n' +
                '\tjclass cls = env->GetObjectClass(obj);\n' +
                '\tjfieldID fid = env->GetFieldID(cls, "_pointer", "J");\n' +
                '\tenv->SetLongField(obj, fid, (__int64)object);\n}\n')

    out_c.write('JNIEXPORT void JNICALL Java_' + jname + '_finalize' +
                '\n(JNIEnv * env, jobject obj) {\n')
    out_c.write('\tjclass cls = env->GetObjectClass(obj);\n' +
                '\tjfieldID fid = env->GetFieldID(cls, "_pointer", "J");\n' +
                '\tjlong var = env->GetLongField(obj, fid);\n' +
                '\t' + name + '* object = (' + name + '*)(__int64)var;\n' +
                '\tdelete object;\n}\n')

    for key in type_conversion.keys():
        pattern = key + r'[ ]+[a-zA-Z0-9_]+(?:[ \n]*[;=])'
        all = re.findall(pattern, text)
        for var in all:
            c_varname = var.replace(key, '').replace(' ', '').replace('\n', '').replace(';', '').replace('=', '')
            varname = c_varname.title()
            out_j.write('\tpublic native ' + type_conversion[key][0] + ' Get' + varname + '();\n')
            out_j.write('\tpublic native void' + ' Set' + varname + '(' + type_conversion[key][0] + ' data);\n')

            out_c.write('\nJNIEXPORT ' + type_conversion[key][1] + ' JNICALL Java_' + jname + '_Get' + varname +
                        '\n(JNIEnv * env, jobject obj) {\n')
            out_c.write('\tjclass cls = env->GetObjectClass(obj);\n' +
                '\tjfieldID fid = env->GetFieldID(cls, "_pointer", "J");\n' +
                '\tjlong var = env->GetLongField(obj, fid);\n' +
                '\t' + name + '* object = (' + name + '*)(__int64)var;\n' +
                '\t' + key + ' result = object->' + c_varname + ';\n' +
                '\treturn (' + type_conversion[key][1] + ')result;\n}\n')
            out_c.write('\nJNIEXPORT void JNICALL Java_' + jname + "_Set" + varname +
                        "\n(JNIEnv * env, jobject obj, " + type_conversion[key][1] + " data) {\n")
            out_c.write('\tjclass cls = env->GetObjectClass(obj);\n' +
                '\tjfieldID fid = env->GetFieldID(cls, "_pointer", "J");\n' +
                '\tjlong var = env->GetLongField(obj, fid);\n' +
                '\t' + name + '* object = (' + name + '*)(__int64)var;\n' +
                '\tobject->' + c_varname + ' = (' + key + ')data;\n}\n')

    out_c.write('#ifdef __cplusplus\n}\n#endif\n#endif\n')
    out_c.close()
    out_j.write('}\n')
    out_j.close()

    compiler_options = 'g++ -I"." -I"' + java_dir + '\\include" -fPIC "' + output_dir + \
                       '\\CPP_sources\\' + jname + '.cpp" -shared -o "' + \
                       output_dir + '\\CPP_LIB\\' + jname + '.so"'
    print(compiler_options)
    print('\n')
    #print(check_output(compiler_options, shell=True))
    os.system(compiler_options)


try:
    os.mkdir(output_dir)
    os.mkdir(output_dir + "\\CPP_sources")
    os.mkdir(output_dir + "\\CPP_LIB")
except:
    print("Unable to create output dir")

for file in files_to_convert:
    source = open(file, 'r')

    is_parsing = False
    brackets = 0
    struct_text = ""
    struct_name = ""

    while True:
        s = source.readline()
        if s == '':
            break
        if is_parsing:
            struct_text += s
            if '{' in s:
                brackets += 1
            if '}' in s:
                brackets -= 1
            if brackets == 0:
                is_parsing = False
                parse_struct(struct_text, struct_name, file)

        if 'struct' in s or 'class' in s:
            if not is_parsing:
                if '{' in s:
                    brackets = 1
                else:
                    brackets = 0
                struct_text = ""
                s = s.replace('\t', '').replace(' ', '').replace('\n', '').replace('struct', '').replace('class', '').replace('{', '')
                is_parsing = True
                struct_name = s
    source.close()
