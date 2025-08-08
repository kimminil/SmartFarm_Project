/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f4xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define door1_Pin GPIO_PIN_0
#define door1_GPIO_Port GPIOC
#define door2_Pin GPIO_PIN_1
#define door2_GPIO_Port GPIOC
#define Peltier1_Pin GPIO_PIN_2
#define Peltier1_GPIO_Port GPIOC
#define Peltier2_Pin GPIO_PIN_3
#define Peltier2_GPIO_Port GPIOC
#define Trig_Pin GPIO_PIN_6
#define Trig_GPIO_Port GPIOA
#define Echo_Pin GPIO_PIN_7
#define Echo_GPIO_Port GPIOA
#define INT_Pin GPIO_PIN_4
#define INT_GPIO_Port GPIOC
#define CS_Pin GPIO_PIN_5
#define CS_GPIO_Port GPIOC
#define DHT11_Pin GPIO_PIN_12
#define DHT11_GPIO_Port GPIOB
#define led2_Pin GPIO_PIN_13
#define led2_GPIO_Port GPIOB
#define Water_Chk_Pin GPIO_PIN_15
#define Water_Chk_GPIO_Port GPIOB
#define Fan_On_Pin GPIO_PIN_6
#define Fan_On_GPIO_Port GPIOC
#define Water_P2_Pin GPIO_PIN_8
#define Water_P2_GPIO_Port GPIOC
#define Water_P1_Pin GPIO_PIN_9
#define Water_P1_GPIO_Port GPIOC
#define Fan_Peltier1_Pin GPIO_PIN_8
#define Fan_Peltier1_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
