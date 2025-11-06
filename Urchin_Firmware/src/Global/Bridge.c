//
// Created by gabri on 11/1/2025.
//

#include "Bridge.h"
#include <stddef.h>
#include <string.h>
#include <stdio.h>



void BridgeInit() {
    //BRIDGEMutex = xSemaphoreCreateBinaryWithCaps();
}
//rolint: ignore
BridgeMotor BRIDGE[BRIDGEMaxNum];

//rolint: ignore
unsigned char BRIDGEsize = 0;


void AddBridge(BridgeMotor* mem){
    memcpy(BRIDGE+BRIDGEsize, mem, sizeof(BridgeMotor));
    BRIDGEsize++;
}

BridgeMotor* GetBridge(const char joint[]) {
    for(int i=0;i<BRIDGEsize;i++) {
        if (strcmp(joint,BRIDGE[i].Joint)==0) {
            return &BRIDGE[i];
        }

    }
    return NULL;
}
