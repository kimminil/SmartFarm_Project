/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
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
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dac.h"
#include "spi.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "MCP2515.h"
#include "CANSPI.h"


//
#define printf_en 1
#define USART_Ch_1_EN	3
#define Console_Ch2   2
#define dht11_en 3
#define Ch1	1
#define cds_en	2
#define co2_en	3
#define w_height_en	4
#define servo_en 5
#define water_pump_en 	6
#define fan_en 6
#define light_en 6
#define pelt_en 6
#include "my_library.h"






/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

//변수 선언

//float temp=0.0;
//float humi=0.0;
//int16_t temp_x10=0;
//int16_t humi_x10=0;
//char message[16];
//uCAN_MSG rxMessage;

char Test_Msg[16];
char pass_sig[] = "Pass\r\n";
char msg_to_Rpi[30];
//char Cmd_Msg[80];
extern int Cmd_values[5];
uint8_t door_flag;
uint8_t door_flg;
//구조체
struct flags{
	uint8_t water_sensor_flag;
	uint8_t timer1;
	uint8_t timer2;
}FLAGS = {0,0,0};
struct flags *flag = &FLAGS;

struct Sensor_Value{
	  float TEMP;		// 온도
	  float RH;			// 습도
	  float lux ;				// 밝기
	  float co2 ;				// c02 ppm
	  float w_1;		// 둘 중 하나
}sen_val = {0.0, 0.0, 0.0, 0.0, 0.0};
struct Sensor_Value *sen_v = &sen_val;


bool detected;
uint8_t Sensor_flag = 0;
uint8_t dis_sensor_flag = 0;
uint8_t water_sensor_flag= 0;
uint8_t door_flag = 0;
uint16_t cnt = 0;
uint8_t timer1 = 0;
uint8_t timer2 = 0;


typedef enum {
    UART_STATE_WAIT_TEST = 0,  // 테스트 모드 대기
    UART_STATE_WAIT_CMD        // 명령 수신 대기
} UART_STATE_t;

volatile UART_STATE_t uart_state = UART_STATE_WAIT_TEST;
volatile uint8_t test_ready = 0;
volatile uint8_t cmd_ready = 0;

char Test_Msg[16] = {0};
extern char Cmd_Msg[16] = {0};




//extern ADC_HandleTypeDef hadc1;


void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);





/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */


/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_NVIC_Init(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_TIM6_Init();
  MX_USART1_UART_Init();
  MX_USART2_UART_Init();
  MX_ADC1_Init();
  MX_TIM1_Init();
  MX_TIM2_Init();
  MX_TIM3_Init();
  MX_TIM4_Init();
  MX_TIM5_Init();
  MX_DAC_Init();
  MX_TIM11_Init();
  MX_SPI1_Init();
  MX_TIM7_Init();

  /* Initialize interrupts */
  MX_NVIC_Init();
  /* USER CODE BEGIN 2 */
  HAL_TIM_Base_Start(&htim6);

  HAL_ADC_Start(&hadc1);
  HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);

  HAL_TIM_Base_Start_IT(&htim2);
  HAL_TIM_Base_Start_IT(&htim3);
  HAL_TIM_Base_Start_IT(&htim4);
  HAL_TIM_Base_Start_IT(&htim5);
  //HAL_TIM_Base_Start_IT(&htim1);
  HAL_TIM_PWM_Start(&htim11, TIM_CHANNEL_1);

  //
  HAL_UART_Receive_IT(&huart1, (uint8_t*)Test_Msg, 16);
  uart_state = UART_STATE_WAIT_TEST;

  fan_off();
  Water_P1_Stop();
  Water_P2_Stop();
  //can_mcp2515_init();
  //CANSPI_Initialize();


  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {



	  if (uart_state == UART_STATE_WAIT_TEST && test_ready)
	      {
	          test_ready = 0;  // 사용 후 초기화
	          Test_Msg[15] = '\0';  // 문자열 종료
	          printf("Received Test Msg: %s\r\n", Test_Msg);

	          if (strcmp(Test_Msg, "STM32 Test Mode") == 0)
	          {
	              printf("Test message matched. Switching to CMD mode.\r\n");

	              uart_state = UART_STATE_WAIT_CMD;

	              if (DHT11_Sensor_Test() && check_light())
	              {
	                  Sensor_flag = 1;
	                  printf("Sensor Check Complete\r\n");
	                  HAL_UART_Transmit(&huart1, (uint8_t*)pass_sig, strlen(pass_sig), 10);
	              }

	              // 명령 수신 준비 시작
	             // HAL_UART_Receive_IT(&huart1, (uint8_t*)Cmd_Msg, 10);
	          }
	          else
	          {
	              // 테스트 메시지 다시 수신 준비
	              HAL_UART_Receive_IT(&huart1, (uint8_t*)Test_Msg, 16);
	          }
	      }

	      else if (uart_state == UART_STATE_WAIT_CMD)
	      {
	          // 센서 데이터 측정
	          float TEMP = DHT11_Run_TEMP();
	          float RH = DHT11_Run_RH();
	          float lux = read_light_lux();
	          float co2 = read_co2();
	          float w_1 = isWaterDetected1();
	          //초음파 제외
	          //HCSR04_Read();


			  //uint32_t distance = Distance;
			  //bool detected = (distance < 6);
			  //door_flag = update_door_state(door_flag, detected);
			  //handle_door_action(door_flag);


	          //printf("TEMP: %.1f RH: %.1f CO2: %.1f LUX: %.1f WATER: %.1f\r\n", TEMP, RH, co2, lux, w_1);
	          if(door_flg == 1){
	        	  door_open();
	        	  door_flg = 0;
	        	  door_stop();
	          }
	          else if(door_flg ==2){
	        	  door_close();
	        	  door_flg = 0;
	        	  door_stop();
	          }
	          else{
	        	  door_stop();
	          }
	          cnt++;
	          if (cnt == 20)  // 약 20초마다 RPi로 전송
	          {
	              cnt = 0;
	              sprintf(msg_to_Rpi, "%.1f,%.1f,%.1f,%.1f,%.1f\r\n", TEMP, RH, co2, lux, w_1);
	              printf("Sending sensor data: %s", msg_to_Rpi);
	              HAL_UART_Transmit(&huart1, (uint8_t*)msg_to_Rpi, strlen(msg_to_Rpi), 100);
	          }
	          HAL_UART_Receive_IT(&huart1, (uint8_t*)Cmd_Msg, 10);
	          HAL_Delay(1000);  // 1초 대기
	      }

	      HAL_Delay(10);

  }


    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */

  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE3);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 4;
  RCC_OscInitStruct.PLL.PLLN = 180;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 2;
  RCC_OscInitStruct.PLL.PLLR = 2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV2;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief NVIC Configuration.
  * @retval None
  */
static void MX_NVIC_Init(void)
{
  /* TIM2_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(TIM2_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(TIM2_IRQn);
}

/* USER CODE BEGIN 4 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{

    if (huart->Instance == USART1)
    {
        if (uart_state == UART_STATE_WAIT_TEST)
        {
            test_ready = 1;
        }
        else if (uart_state == UART_STATE_WAIT_CMD)
        {
            Cmd_Msg[10] = '\0';
            printf("Cmd_Msg = %s\r\n", Cmd_Msg);

            parse_fixed_csv(Cmd_Msg);

            if (Cmd_values[0] == 1)
            {
            	printf("\n\n======Actuactor start by Sensor Value======\r\n");
                for (int i = 0; i < 5; i++)
                    printf("Sensor Cmd_values[%d] = %d\r\n", i, Cmd_values[i]);
                process_commands(Cmd_values);
                printf("=====================================================\r\n\n\n");
            }
            else
            {
            	printf("\n\n======Actuactor start by Manual Control======\r\n");
                for (int i = 0; i < 5; i++)
                    printf("\n\nManual Cmd_values[%d] = %d\r\n", i, Cmd_values[i]);
                manual_process(Cmd_values);
                printf("=====================================================\r\n\n\n");
            }

            // 다음 수신 준비
        }
        HAL_UART_Receive_IT(&huart1, (uint8_t*)Cmd_Msg, 10);
    }
}



/* USER CODE END 4 */

/**
  * @brief  Period elapsed callback in non blocking mode
  * @note   This function is called  when TIM14 interrupt took place, inside
  * HAL_TIM_IRQHandler(). It makes a direct call to HAL_IncTick() to increment
  * a global variable "uwTick" used as application time base.
  * @param  htim : TIM handle
  * @retval None
  */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
  /* USER CODE BEGIN Callback 0 */


	if (htim->Instance == TIM2)
	{	//	수위 실시간 인터럽트로 측정
		if(Sensor_flag == 1)
		{

			float light = read_light();				// 빛세기 adc로 읽기
			light_on((uint16_t)light);				// lux 구하기
			float w_2 = isWaterDetected1();			// 수위센서
			if(w_2 == 0.0){							// 수위 센서 측정 x
				Water_P1_Start(); //급수

			}else{									// 수위 센서 측정 o
				Water_P1_Stop();
			}

		}
	}
	if (htim->Instance == TIM3)
	{	// 30s초마다 인터럽트 발생하는 코드 => 1시간 경과를 측정하는 인터럽트
		if(Sensor_flag == 1)
		{
			(flag->timer1)+=1;									// 30초 마다 카운트

				//시간 경과 측정
			//printf("%.1f min left tp start\r\n", ((10 -flag->timer1)/2.0));

			if(flag->timer1 == 10){							//5분 마다 배수

				flag->water_sensor_flag = 1;					// 배수flag = 1
				printf("Water Drainage Start\r\n");
			}
			else if(flag -> timer1 == 16){						// 배수 flag  3분간 1로 고정

				flag->timer1 = 0;								// 배수 후 0으로 초기화
				flag->water_sensor_flag = 0;
				printf("Water Drainage Stop\r\n");
			}
			if(flag->timer1 > 10){
				printf("%.1f min left to stop\r\n", (16 - flag->timer1)/2.0);
			}
			els{
				printf("%.1f min left tp start\r\n", ((10 -flag->timer1)/2.0));
			}

		}
	}



	if (htim->Instance == TIM5)
	{	//
		// 0.1초마다 배수 플레그 확인
		if(Sensor_flag == 1){

			if(flag->water_sensor_flag == 1){
				//printf("Water drainage Start\r\n");
				Water_P2_Start();

			}else{
				//printf("Water drainage Stop\r\n");
				Water_P2_Stop();

			}
		}
	}

  /* USER CODE END Callback 0 */
  if (htim->Instance == TIM14)
  {
    HAL_IncTick();
  }
  /* USER CODE BEGIN Callback 1 */

  /* USER CODE END Callback 1 */
}

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
