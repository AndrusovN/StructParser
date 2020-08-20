# StructParser
Script to parse c++ strucrures and port them to java code

I realized that it is usual situation when part of project programmed with one language and another part - with another language. In my situation it was c++ and java.
So I had to use same structures in c++ and java and pass them via the internet. For example I have client part in C++, then send message with data about user to Java server 
and it should deserialize this message to same data about user.

But it's good idea to use principle DRY (Don't Repeat Yourself) so it's bad to write structure twice in different languages. That's why I wanted to make program that will
create java code from c++ code.

This is a very first variant, but it works. Using it you can create java classes from c++ structures in .h files.

To run this program you will need:
1. Java development kit (it's better to use 9.x version, because I tried with it. But you can try with another versions - I'm not sure this will work)
2. g++ 64 bit to compile c++ code
3. .h files with your structures (now this program does not support structures wich realizations are in .cpp files - put it all in .h or wait for newer version :) )
4. python interpretator to run script

Now about program:
Run it from cmd. You can use these parameters:

	-f "PATH\FILE.h" to pass .h file with structures (you can use many -f parameters)
	
	-o "PATH\FOLDER" to set output directory
	
	-java "PATH\FOLDER" to set jdk directory. For example for me it's "C:\Program Files\Java\jdk-9.0.4"

For example you can use Test.h file - it has two structures:

	cd PATH\StructParser
	
	StructParser.py -f "Test.h" -o "out" -java "C:\Program Files\Java\jdk-9.0.4"

This will do all work. Then in folder out you will find .java files.

This program will parse each file and for each struct it will create java class with name "YourStructNameJ" so it adds "J" to the end. And .java file
Also for each struct it generates .cpp JNI file in "YOUR_OUTPUT_DIRECTORY\CPP_sources" and compiles this file to .so file to "YOUR_OUTPUT_DIRECTORY\CPP_LIB"
This .so file is dynamic library which java will load in runtime. It has definitions of all native functions in generated java class. 
Java .class file should find this file by path "CPP_LIB\THIS_FILE_NAME.so"

Java class contains empty constructor and Get/Set method for each variable in your struct. It has finilize method (don't use it - it is for garbage collector).
And init function is system function, which initialize class, using c++ code.
Also it has field _pointer: please don't use it - it is system field which
connects c++ and java code. If you change it, everything can die and world will crash with error 4996.

Also this program is in very first version so it can convert only simple types (int, long, char, bool, unsigned, short)

If there is compilation error while running this program, it provides string which compiles code using g++. 
You can copy it to cmd and see compiler errors or you can look for compiler parameters and use another compiler if you want.

I hope this program will help you with connecting c++ and java code.
