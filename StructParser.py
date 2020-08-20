import sys
import re
import os
import subprocess

sys_path = sys.argv[0].replace("StructParser.py", '')
help_path = sys_path + "help.info"
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


def help():
    try:
        f_help = open(help_path, 'r')
        print(''.join(f_help.readlines()))
        f_help.close()
    except:
        print("Error! Cannot read help file:\n" + help_path)
    quit()

f_conv.close()
files_to_convert = []
i = 0
MAX_RECURSION_LEVEL = 10
output_dir = "."
java_dir = "C:\\Program Files\\Java\\jdk-9.0.4"
include_paths = ['.']
STOP_IF_ERROR = False
additional_compiler_options = ['-shared', '-o']
java_compiler_options = []

if len(sys.argv) == 1:
    help()

while i < len(sys.argv):
    p = sys.argv[i]
    if p == '--help':
        help()
    elif p == '-es':
        STOP_IF_ERROR = True
    elif p == '-ec':
        STOP_IF_ERROR = False
    elif i < len(sys.argv) - 1:
        if p == '-f':
            if sys.argv[i+1].split('.')[-1].upper() in ok_extensions:
                files_to_convert.append(sys.argv[i + 1])
                i += 1
        elif p == '-o':
            output_dir = sys.argv[i + 1]
            i += 1
        elif p == '-java':
            java_dir = sys.argv[i + 1]
            i += 1
        elif p == '-I':
            include_paths.append(sys.argv[i + 1])
            i += 1
        elif p == '-mrl':
            MAX_RECURSION_LEVEL = int(sys.argv[i + 1])
            i += 1
        elif p == '-cc':
            additional_compiler_options.append(sys.argv[i + 1])
            i += 1
        elif p == '-jc':
            java_compiler_options.append(sys.argv[i + 1])
            i += 1
    i += 1

print('Converting files:\n' + str(files_to_convert))
java_files = []

def extract_defines(text):
    ptrn1 = r'#define[ \n\t]+[a-zA-Z0-9_]+[ \n\t]+[a-zA-Z0-9_:]+'
    defines = re.findall(ptrn1, text)
    for d in defines:
        ds = d.replace(';', '').split()[1:]
        if len(ds) == 2:
            to_add = []
            for key in type_conversion.keys():
                if key == ds[1]:
                    to_add = [type_conversion[key][0], type_conversion[key][1]]
                    break
            type_conversion[ds[0]] = to_add


def extract_typedefs(text):
    ptrn = r'typedef[ \n\t]+[a-zA-Z0-9_:]+[ \n\t]+[a-zA-Z0-9_]+;'
    typedefs = re.findall(ptrn, text)
    for t in typedefs:
        ts = t.replace(';', '').split()[1:]
        to_add = []
        for key in type_conversion.keys():
            if key == ts[0]:
                to_add = [type_conversion[key][0], type_conversion[key][1]]
                break
        type_conversion[ts[1]] = to_add


def extract_includes(text):
    include_ptrn = r'#include[ \n\t]+[<"][a-zA-Z0-9_]+(?:[.][a-zA-Z0-9_]+){0,1}[>"]'
    return list(map(lambda x: x.replace(';', '').split()[1].replace('"', '').replace('<', '').replace('>', ''),
                        re.findall(include_ptrn, text)))


def search_type(type_name, files_to_search, filepath, recursion_level=0):
    if recursion_level < MAX_RECURSION_LEVEL:
        for p in include_paths + [filepath]:
            for f in files_to_search:
                if f in os.listdir(p):
                    src = open(p + '\\' + f, 'r')
                    lns = src.readlines()
                    src.close()
                    text = ''.join(lns)
                    extract_typedefs(text)
                    extract_defines(text)

                    n_struct_text = ''
                    n_brackets = 0
                    found = False
                    for ln in lns:
                        if found:
                            if '{' in ln:
                                n_brackets += 1
                            if n_brackets == 1:
                                n_struct_text += ln
                            if '}' in ln:
                                n_brackets -= 1
                            if n_brackets == 0:
                                break
                        if 'struct ' in ln and ';' not in ln:
                            nln = ln.replace('\t', '').replace(' ', '').replace('\n', '')\
                                .replace('struct', '').replace('{', '')
                            if nln == type_name:
                                found = True
                                if '{' in ln:
                                    n_brackets += 1

                    if found:
                        parse_struct(n_struct_text, type_name, p + '\\' + f, extract_includes(text))
                        return True

                    if type_name not in type_conversion.keys():
                        incs = extract_includes(text)
                        if search_type(type_name, incs, p, recursion_level+1):
                            return True
                    else:
                        return True
        return False
    else:
        return False


def parse_struct(text, name, filename, includes):
    print(name)
    jname = name + 'J'
    out_j = open(output_dir + "\\" + jname + '.java', 'w')
    out_j.write('public class ' + jname + ' {\n')
    out_j.write('\tstatic {\n\t\tSystem.load(' + jname +
        '.class.getProtectionDomain().getCodeSource().getLocation().getPath().substring(1).replaceAll("/","\\\\\\\\")' +
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

    out_c.write('\n' + name + ' * get_' + name + '(JNIEnv * env, jobject obj) {\n' +
                '\tjclass cls = env->GetObjectClass(obj);\n' +
                '\tjfieldID fid = env->GetFieldID(cls, "_pointer", "J");\n' +
                '\tjlong var = env->GetLongField(obj, fid);\n' +
                '\t' + name + '* object = (' + name + '*)(__int64)var;\n'
                '\treturn object;\n}\n')

    out_c.write('JNIEXPORT void JNICALL Java_' + jname + '_finalize' +
                '\n(JNIEnv * env, jobject obj) {\n')
    out_c.write('\t' + name + '* object = get_' + name + '(env, obj);\n' +
                '\tif(object != 0) {\n\t\tdelete object;\n\t\tobject = 0;\n\t}\n}\n')

    p1 = r'(?:[ ]+[*a-zA-Z0-9_]+(?:[ \n]*(?:=[a-zA-Z0-9:_ \n\(\)]+)*)*)'
    pattern = \
        r'[a-zA-Z0-9_:]+' + p1 + '(?:,' + p1 + ')*' + ';'
    all = re.findall(pattern, text)
    vars = {}

    filepath = '\\'.join(filename.split('\\')[:-1]) if '\\' in filename else '.'

    for s in all:
        t = s.split(' ')[0]
        w = list(map(lambda x: x.replace(' ', '').split('=')[0], re.findall(p1, s)))
        for var in w:
            vars[var] = t
    for var in vars.keys():
        key = vars[var]
        c_varname = var.replace(key, '').replace(' ', '').replace('\n', '').replace(';', '').replace('=', '')
        varname = c_varname.title()
        if key not in type_conversion:
            res = search_type(key, includes, filepath)
            if not res:
                print('ERROR! Unknown type \'' + key + '\'.')
                if STOP_IF_ERROR:
                    print('PROGRAM FINISHED!')
                    out_c.close()
                    out_j.close()
                    quit()
                else:
                    print('PROGRAM IGNORED FIELD \'' + c_varname + '\'')
                    continue
        out_j.write('\tpublic native ' + type_conversion[key][0] + ' Get' + varname + '();\n')

        out_c.write('\nJNIEXPORT ' + type_conversion[key][1] + ' JNICALL Java_' + jname + '_Get' + varname +
                    '\n(JNIEnv * env, jobject obj) {\n')
        out_c.write('\t' + name + '* object = get_' + name + '(env, obj);\n')
        if type_conversion[key][1] != 'jobject':
            out_j.write('\tpublic native void' + ' Set' + varname + '(' + type_conversion[key][0] + ' data);\n')

            out_c.write(
                '\t' + key + ' result = object->' + c_varname + ';\n' +
                '\treturn (' + type_conversion[key][1] + ')result;\n}\n')
            out_c.write('\nJNIEXPORT void JNICALL Java_' + jname + "_Set" + varname +
                        "\n(JNIEnv * env, jobject obj, " + type_conversion[key][1] + " data) {\n")
            out_c.write('\t' + name + '* object = get_' + name + '(env, obj);\n' +
                        '\tobject->' + c_varname + ' = (' + key + ')data;\n}\n')
        else:
            out_c.write('\tjclass cls = env->FindClass("' + type_conversion[key][0] + '");\n' +
                        '\tjmethodID constructor = env->GetMethodID(cls, "<init>", "(J)V");\n' +
                        '\tjobject result = env->NewObject(cls, constructor, (jlong)&(object->' + c_varname + '));\n' +
                        '\treturn result;\n}\n')


    out_c.write('#ifdef __cplusplus\n}\n#endif\n#endif\n')
    out_c.close()
    out_j.write('}\n')
    out_j.close()

    compiler_options = 'g++ -I"' + java_dir + '\\include" '
    for ipath in include_paths:
        compiler_options += '-I"' + ipath + '" '
    compiler_options += '-fPIC "' + output_dir + \
                        '\\CPP_sources\\' + jname + '.cpp" '
    for co in additional_compiler_options:
        compiler_options += co + ' '
    compiler_options += '"' + output_dir + '\\CPP_LIB\\' + jname + '.so"'
    print(compiler_options)
    print('\n')
    #print(check_output(compiler_options, shell=True))
    os.system(compiler_options)
    java_files.append(output_dir + "\\" + jname + '.java')
    type_conversion[name] = [jname, 'jobject']


try:
    os.mkdir(output_dir)
    os.mkdir(output_dir + "\\CPP_sources")
    os.mkdir(output_dir + "\\CPP_LIB")
except:
    print("Unable to create output dir")

struct_names = []

for file in files_to_convert:
    source = open(file, 'r')

    is_parsing = False
    brackets = 0
    struct_text = ""
    struct_name = ""

    all_file = ''
    lines = []
    while True:
        s = source.readline()
        all_file += s
        lines.append(s)
        if s == '':
            break
    source.close()

    extract_typedefs(all_file)

    extract_defines(all_file)

    includes = extract_includes(all_file)

    for line in lines:
        if is_parsing:
            if '{' in line:
                brackets += 1

            if brackets == 1:
                struct_text += line

            if '}' in line:
                brackets -= 1

            if brackets == 0:
                is_parsing = False
                parse_struct(struct_text, struct_name, file, includes)

        if 'struct' in line:
            if not is_parsing:
                if '{' in line:
                    brackets = 1
                else:
                    brackets = 0
                struct_text = ""
                line = line.replace('\t', '').replace(' ', '').replace('\n', '').replace('struct', '').replace('{', '')
                is_parsing = True
                struct_name = line
                struct_names.append(struct_name)


java_compile = '"' + java_dir + '\\bin\\javac.exe" '

for op in java_compiler_options:
    java_compile += op + ' '

for java_file in java_files:
    java_compile += '"' + java_file + '" '
java_compile += '-d "' + output_dir + '"'
print(java_compile)
subprocess.call(java_compile)