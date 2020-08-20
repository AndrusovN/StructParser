# StructParser
Script to parse c++ strucrures and port them to java code

## Motivation
I realized that it is usual situation when part of project programmed with one language and another part - with another language. In my situation it was c++ and java.
So I had to use same structures in c++ and java and pass them via the internet. For example I have client part in C++, then send message with data about user to Java server 
and it should deserialize this message to same data about user.

But it's good idea to use principle DRY (Don't Repeat Yourself) so it's bad to write structure twice in different languages. That's why I wanted to make program that will
create java code from c++ code.

This is a very first variant, but it works. Using it you can create java classes from c++ structures in .h files.

## What do you need ti run this program

To run this program you will need:
1. Java development kit (it's better to use 9.x version, because I tried with it. But you can try with another versions - I'm not sure this will work)
2. g++ 64 bit to compile c++ code
3. .h files with your structures (now this program does not support structures wich realizations are in .cpp files - put it all in .h or wait for newer version :) )
4. python interpretator to run script


## How it works

Now about program:
Run it from cmd. You can use these parameters:

	-f "PATH\FILE" to choose files to port to java (to use many files, print many flags -f)
	
	-o "PATH\FOLDER" to set output folder (there you will find .java .cpp and .so files) (if this path does not exists, it will be automatically generated) (default value is '.\')
	
	-java "PATH" to set folder with java (for example -java "C:\Program Files\Java\jdk-9.0.4" is default value)
	
	-I "PATH" to add include path
	
	-mrl <number> to set maximum recursion level in searching included files (for example -mrl 10) (default value is 10)
	
	-cc "SOME OPTION" to add g++ compiler option (for example -cc "-Wall")
	
	-jc "SOME OPTIO" to add javac compiler option (for example -jc "-Xlint:deprecation")
	
	-es to stop program in case of error
	
	-ec to continue program running in case of error
	
	--help to get this text again

For example you can use Test.h file - it has two structures:

	cd PATH\StructParser
	
	StructParser.py -f "Test.h" -o "out" -java "C:\Program Files\Java\jdk-9.0.4" -I include -cc "-Wall" -jc "-Xlint:deprecation" -es -mrl 5

This will do all work. Then in folder out you will find .java files.

This program will parse each file and for each struct it will create java class with name "YourStructNameJ" so it adds "J" to the end. And .java file
Also for each struct it generates .cpp JNI file in "YOUR_OUTPUT_DIRECTORY\CPP_sources" and compiles this file to .so file to "YOUR_OUTPUT_DIRECTORY\CPP_LIB"
This .so file is dynamic library which java will load in runtime. It has definitions of all native functions in generated java class. 
Also it compiles .java files to .class files. If you move you .class or .java files, don't forget to move .so files the same way. So if you have C:\PATH\YOUR_CLASS.class,
you also have to have C:\PATH\CPP_LIB\YOUR_CLASS.so file

Java class contains empty constructor and Get/Set method for each variable in your struct. It has finilize method (don't use it - it is for garbage collector).
And init function is system function, which initialize class, using c++ code.
Also it has field _pointer: please don't use it - it is system field which
connects c++ and java code. If you change it, everything can die and world will crash with error 4996.

Also this program is in very first version so it can convert only simple types (int, long, char, bool, unsigned, short)

If there is compilation error while running this program, it provides string which compiles code using g++. 
You can copy it to cmd and see compiler errors or you can look for compiler parameters and use another compiler if you want.

## About arrays
Arrays in c++ and java are very different. In c++ it's just pointer to the first item, when in java it is special java type.
That's why it is not an easy task to convert c++ array to java array.
If you use an array in your struct you also have to know it's length. (OK, length of some c++ char arrays could be found by searching for terminating symbol, 
but this type of arrays is not supported yet).

So let's imagine such simple struct:
    struct MyStruct {
		char * my_name;
		int my_size;
	}
Where my_size is the size of name. To make StructParser know that relation between my_name variable and my_size variable, include "structparser.h" file
from root of repository and use __ARRAY__(size_variable_name) instead of "*" symbol.
    #include "structparser.h" //Included from C:\Projects\GitHub\StructParser
	struct MyStruct {
		char __ARRAY__(my_size) my_name;
		int my_size;
    }
	
StructParser will generate methods to get java char[], to set it, with java char[] and to change one array item.
Sadly now StructParser supports only one-dimentional arrays.

I hope this program will help you with connecting c++ and java code.
