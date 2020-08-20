#include <iostream>
#include "include.h"
#include "structparser.h"

enum a {

};

struct AnotherStruct
{
    MyStruct1 __ARRAY__(size) data;
    int size;

    /*
    int anotherHiddenInt;
    bool hiddenBool;
    */

    //int hiddenInd;
};
