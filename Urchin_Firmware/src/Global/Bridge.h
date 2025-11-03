//
// Created by gabri on 11/1/2025.
//

#ifndef BRIDGE_H
#define BRIDGE_H

#define BRIDGEMaxNum 253
#define BRIDGEMaxBrand 30
#define BRIDGEMaxModel 10
#define BRIDGEMaxName 50


#ifdef __cplusplus
extern "C" {
#endif

    #pragma pack(push, 1)  // No padding between fields
#include <stdbool.h>

typedef struct{
        unsigned int Num;
        char Brand[BRIDGEMaxBrand];
        char Model[BRIDGEMaxModel];
        char Joint[BRIDGEMaxName];
        int BoundsMin;
        int BoundsMax;
        int AlignmentAngle;
        bool NextNode;
    }BridgeMotor;

    extern BridgeMotor BRIDGE[BRIDGEMaxNum];
    extern unsigned char BRIDGEsize;

    void Bridgeinit();

#ifdef __cplusplus
}
#endif

#endif //BRIDGE_H
