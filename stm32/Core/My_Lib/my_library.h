
#ifndef __my_uart_lib__
#define __my_uart_lib__

#include <stdarg.h>
#include <math.h>
#include "main.h"
#include <stdio.h>
//변수 선언

//시작 선언 변수
extern char Start_Msg[16];
extern char msg[64];
uint16_t map(uint16_t value, uint16_t in_min, uint16_t in_max, uint16_t out_min, uint16_t out_max);
//============================================================================================================
// ============================================printf문 =======================================================
//============================================================================================================

#if printf_en
extern int __io_putchar(int ch)
{
#if Console_Ch1
    //UART_HandleTypeDef huart1;
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, 0xFFFF);

#elif Console_Ch2
    //UART_HandleTypeDef huart2;
    HAL_UART_Transmit(&huart2, (uint8_t *)&ch, 1, 0xFFFF);

#elif Console_Ch3
    //UART_HandleTypeDef huart3;
    HAL_UART_Transmit(&huart3, (uint8_t *)&ch, 1, 0xFFFF);

#elif Console_Ch4
    //UART_HandleTypeDef huart4;
    HAL_UART_Transmit(&huart4, (uint8_t *)&ch, 1, 0xFFFF);

#elif Console_Ch5
    //UART_HandleTypeDef huart3;
    HAL_UART_Transmit(&huart5, (uint8_t *)&ch, 1, 0xFFFF);

#elif Console_Ch6
    //UART_HandleTypeDef huart3;
    HAL_UART_Transmit(&huart6, (uint8_t *)&ch, 1, 0xFFFF);
#endif
    __NOP();
  return ch;
}
#endif

//uart  통신용
void vprint(uint8_t ch, const char *fmt, va_list argp)
{
    char string[200];
    if(0 < vsprintf(string,fmt,argp)) // build string
    {
      // 2022, 11, 28수정 = Ver 3.2
     #ifdef USART_Ch_1_EN
     	if(ch == 1) HAL_UART_Transmit(&huart1, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_2_EN
     	if(ch == 2) HAL_UART_Transmit(&huart2, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_3_EN
     	if(ch == 3) HAL_UART_Transmit(&huart3, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_4_EN
     	if(ch == 4) HAL_UART_Transmit(&huart4, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_5_EN
   	    if(ch == 5) HAL_UART_Transmit(&huart5, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_6_EN
  	    if(ch == 6) HAL_UART_Transmit(&huart6, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif
    }
}

void my_printf(uint8_t ch, const char *fmt, ...) // custom printf() function
{
  va_list argp;
  va_start(argp, fmt);
  vprint(ch, fmt, argp); // 2023, 9, 12 수정 = 멤버변수 추가 = Ver4.4
  va_end(argp);
}







//===============================================================================================
//=================================온 습도 센서====================================================
//===============================================================================================
#if dht11_en

struct DHT11
{
  int8_t dht11_ch;
  int16_t while_cnt;
  uint16_t old_temp;
  uint16_t old_rh;
  uint16_t dht_time;
  uint8_t Temp_Ch1_dis;
  uint8_t Hum_Ch1_dis;
  uint8_t Temp_Ch2_dis;
  uint8_t Hum_Ch2_dis;
}dht_11_ch1 = {1, 0, 0, 0, 0, 0, 0};
struct DHT11 *dht_ch1 = &dht_11_ch1;

// GPIO Pin Set
  #define DHT11_PORT  DHT11_GPIO_Port // main.h 참고
  #define DHT11_PIN   DHT11_Pin       // main.h 참고

// usec delay
void delay (uint16_t time)
{
 /* change your code here for the delay in microseconds */
 __HAL_TIM_SET_COUNTER(&htim6, 0);
 while ((__HAL_TIM_GET_COUNTER(&htim6)) < time);  // 타이머 7
}

void Set_Pin_Output (GPIO_TypeDef *GPIOx, uint16_t GPIO_Pin)
{
 GPIO_InitTypeDef GPIO_InitStruct = {0};
 GPIO_InitStruct.Pin = GPIO_Pin;
 GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
 GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
 HAL_GPIO_Init(GPIOx, &GPIO_InitStruct);
}

void Set_Pin_Input (GPIO_TypeDef *GPIOx, uint16_t GPIO_Pin)
{
 GPIO_InitTypeDef GPIO_InitStruct = {0};
 GPIO_InitStruct.Pin = GPIO_Pin;
 GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
 GPIO_InitStruct.Pull = GPIO_PULLUP;
 HAL_GPIO_Init(GPIOx, &GPIO_InitStruct);
}

void DHT11_Start (void)
{
 if(dht_ch1 -> dht11_ch == 1)
   { //ch1
   Set_Pin_Output (DHT11_PORT, DHT11_PIN);  // set the pin as output
   HAL_GPIO_WritePin (DHT11_PORT, DHT11_PIN, 0);   // pull the pin low
   delay(18000);   // wait for 18ms
   HAL_GPIO_WritePin (DHT11_PORT, DHT11_PIN, 1);   // pull the pin high
   delay (20);   // wait for 20us
   Set_Pin_Input(DHT11_PORT, DHT11_PIN);    // set as input
   }
}

uint8_t DHT11_Check_Response (void)
{
 uint8_t Response = 0;
 delay (40);
 if(dht_ch1 -> dht11_ch == 1)
  { //ch1
   if (!(HAL_GPIO_ReadPin (DHT11_PORT, DHT11_PIN)))
    {
     delay (80);
      	  if ((HAL_GPIO_ReadPin (DHT11_PORT, DHT11_PIN))) Response = 1;
     else Response = -1; // 255
    }
   while (HAL_GPIO_ReadPin(DHT11_PORT, DHT11_PIN))
     {
	   // wait for the pin to go low
	   dht_ch1 -> while_cnt++;
	   if( dht_ch1 -> while_cnt > 500) break;
     }
   dht_ch1 -> while_cnt = 0;
  }
#endif
 return Response;
}
uint8_t DHT11_Read ()
{
 uint8_t i,j;
 if(dht_ch1 -> dht11_ch == 1)
  {
   for (j=0;j<8;j++)
    {
	  while (!(HAL_GPIO_ReadPin (DHT11_PORT, DHT11_PIN)))
	   {
		  dht_ch1 -> while_cnt++;
		// wait for the pin to go high
		if(dht_ch1 -> while_cnt > 500) break;
	   }
	  dht_ch1 -> while_cnt = 0;
	  delay (40);   // wait for 40 us
	  if (!(HAL_GPIO_ReadPin (DHT11_PORT, DHT11_PIN)))   // if the pin is low
	   {
	    i&= ~(1<<(7-j));   // write 0
	   }
	  else i|= (1<<(7-j));  // if the pin is high, write 1
	  while ((HAL_GPIO_ReadPin (DHT11_PORT, DHT11_PIN)))
	   {
		  dht_ch1 -> while_cnt++;
		// wait for the pin to go low
		if(dht_ch1 -> while_cnt > 500) break;
	   }
	  dht_ch1 -> while_cnt =  0;
    } // for end
  } // if-end
 return i;
}

uint8_t DHT11_Sensor_Test()
{
	uint8_t Rh_byte1, Rh_byte2, Temp_byte1, Temp_byte2;
	uint16_t SUM, RH, TEMP;
	float Temperature = 0;
	float Humidity = 0;
	uint8_t Presence = 0;
 // DHT11 Run == Main
 DHT11_Start();
 Presence = DHT11_Check_Response();
 Rh_byte1 = DHT11_Read ();
 Rh_byte2 = DHT11_Read ();
 Temp_byte1 = DHT11_Read ();
 Temp_byte2 = DHT11_Read ();
 SUM = DHT11_Read();

 // 정수부만 출력 됨
 TEMP = Temp_byte1;
 RH = Rh_byte1;
 // 소수점 부도 출력 됨
 Temperature = (float) TEMP;
 Humidity = (float) RH;

 if(dht_ch1 -> dht11_ch == 1)
  {
	if(TEMP >= 255) Temperature = dht_ch1 -> old_temp;
	else dht_ch1 -> old_temp = Temperature;

	if(RH >= 255) Humidity =dht_ch1 -> old_rh;
	else dht_ch1 -> old_rh = Humidity;

	dht_ch1 -> Temp_Ch1_dis = Temperature;
	dht_ch1 -> Hum_Ch1_dis = Humidity;
  }
 HAL_Delay(500);
 if (TEMP != 0 ||  RH != 0) return 1;


}
float DHT11_Run_RH()
{
	if(DHT11_Sensor_Test()) return dht_ch1 -> Hum_Ch1_dis;
}

float DHT11_Run_TEMP()
{
	if(DHT11_Sensor_Test()) return dht_ch1 -> Temp_Ch1_dis;
}
#endif
// ========================================================조도센서=============================================
#if cds_en
struct cds
{
  int8_t cds_ch;
  uint16_t adc_v;
  uint16_t old_ch1;
  uint16_t old_ch2;
  float cds_Ch1_dis;
  float cds_Ch2_dis;
}Cds_ch1 = {1, 0, 0, 0,0};
struct cds *cds_ch1 = &Cds_ch1;
uint8_t check_light(){
	uint32_t adc_val = 0;
	float lux = 0.0;
	char light_msg[64];
	float r_fixed = 10000.0f; // 10kΩ 고정 저항
    if(cds_ch1 -> cds_ch == 1)
    {
    	ADC_ChannelConfTypeDef sConfig = {0};
    	sConfig.Channel = ADC_CHANNEL_0;
    	sConfig.Rank = 1;
    	sConfig.SamplingTime = ADC_SAMPLETIME_15CYCLES;
    	HAL_ADC_ConfigChannel(&hadc1, &sConfig);
    	HAL_ADC_Start(&hadc1);
        if(HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK)
        {
			adc_val = HAL_ADC_GetValue(&hadc1);
			cds_ch1 ->  adc_v = adc_val;
			if(adc_val == 4095 || adc_val == 0) adc_val = cds_ch1 -> old_ch1;
			else cds_ch1 -> old_ch1 = adc_val;
			float Vout = (adc_val / 4095.0f) * 3.3f;
			float RLDR = (3.3f - Vout) * 10000.0f / (Vout > 0.0f ? Vout : 1.0f);
			float Rk = RLDR / 1000.0f;
			float lux = 63.0f * powf(Rk, -0.7f)+50;
			cds_ch1 ->  cds_Ch1_dis = lux;
    	}
    }
    HAL_ADC_Stop(&hadc1);
    if(adc_val != 4095 || adc_val != 0) return 1;
    else return 0;
    }
float read_light(){
	if(check_light()) return cds_ch1 ->  adc_v;
}
float read_light_lux(){
	if(check_light()) return cds_ch1 ->  cds_Ch1_dis;
}

#endif
// ========================================================이산화탄소센서=============================================
#if co2_en
struct co2
{
  int8_t co2_ch;
  uint16_t old_ch1;
  uint16_t old_ch2;
  float co2_Ch1_dis;
  float co2_Ch2_dis;
}Co2_ch1 = {1, 0, 0, 0,0};
struct co2 *co2_ch1 = &Co2_ch1;


float get_co2_step(uint32_t adc_val) {
    // 12비트 ADC 기준 (0~4095)
//    if (adc_val < 1000) return 0;           //0: < 약 700 ppm  //
//    else if (adc_val < 2000) return 1;      //1: 700~1000 ppm
//    else if (adc_val < 3000) return 2;      //2: 1000~2000 ppm
    float Vref = 3.3; // OR 5.0
	float Vout;
	float CO2_ppm;


	Vout = (adc_val / 4095.0) * Vref;

	//센서를 만든 회사가 배포하는 PDF 문서에서 확인합니다.PWM 출력에 대한 예시:0.4V = 400 ppm2.0V = 5000 ppm
	CO2_ppm = ((Vout - 0.4) / (2.0 - 0.4) ) * (5000 - 400) + 400;
	//printf("vout = %.1f ,Co2 ppm = %.1f\r\n",Vout, CO2_ppm);
	return CO2_ppm;                        //3: >2000 ppm
}



uint8_t check_co2() {
	uint32_t adc_val = 0;
	ADC_ChannelConfTypeDef sConfig = {0};
	sConfig.Channel = ADC_CHANNEL_1;
	sConfig.Rank = 1;
	sConfig.SamplingTime = ADC_SAMPLETIME_15CYCLES;
	HAL_ADC_ConfigChannel(&hadc1, &sConfig);
	HAL_ADC_Start(&hadc1);
    if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK)
    {
    	adc_val = HAL_ADC_GetValue(&hadc1);


    	if(adc_val == 4095 || adc_val == 0) adc_val = co2_ch1 -> old_ch1;
    	else co2_ch1 -> old_ch1 = adc_val;

    	co2_ch1 ->  co2_Ch1_dis = get_co2_step(adc_val);
	}
    HAL_ADC_Stop(&hadc1);
    //printf("adc_val2=%d\r\n", adc_val);
    //printf("CO2 PP, = %0.1f\r\n",co2_ch1 ->  co2_Ch1_dis);
    if(adc_val != 4095 || adc_val != 0) return 1;
    else return 0;
    }
float read_co2(){
	if(check_co2()) return co2_ch1 ->  co2_Ch1_dis;
}
#endif
// ========================================================이산화탄소센서=============================================










#if w_height_en
struct w_height
{
  int8_t w_height_ch;
  uint16_t old_ch1;
  uint16_t old_ch2;
  float w_height_Ch1_dis;
  float w_height_Ch2_dis;
}W_height_ch1 = {1, 0, 0, 0,0};
struct w_height *w_height_ch1 = &W_height_ch1;
struct w_height W_height_ch2 = {1, 0, 0, 0,0};
struct w_height *w_height_ch2 = &W_height_ch2;

struct w_h
{
	uint8_t w1_h;
	uint8_t w2_h;
}W_h = {0,0};
struct w_h *w_h = &W_h;


//비접촉 방식
float isWaterDetected1()
{
	w_h->w1_h = HAL_GPIO_ReadPin(Water_Chk_GPIO_Port, Water_Chk_Pin);
	return (float)(w_h->w1_h == GPIO_PIN_SET);
}

float isWaterDetected2()
{
	w_h->w2_h = HAL_GPIO_ReadPin(Water_Chk_GPIO_Port, Water_Chk_Pin);
	return (float)(w_h->w2_h == GPIO_PIN_SET);
}
#endif
//===========================================Actuator===================================

//===========================================서보===================================
#if servo_en


//
#endif
//===========================================ETC===================================
//===========================================Parsing===================================


#define MAX_VALUES 5
#define MAX_STR_LEN 20
int Cmd_values[5];
void parse_fixed_csv(char* input) {
    char temp[10] = {0};
    int temp_idx = 0;
    int val_idx = 0;

    for (int i = 0; input[i] != '\0' && val_idx < 5; i++) {
        if (input[i] == ',' || input[i] == '\n' || input[i] == '\r') {
            if (temp_idx > 0) {
            	Cmd_values[val_idx++] = atoi(temp);
            	printf(Cmd_values[val_idx-1]);
                temp_idx = 0;
                memset(temp, 0, sizeof(temp));
            }
        } else {
            if (temp_idx < sizeof(temp) - 1) {
                temp[temp_idx++] = input[i];
            }
        }
    }
    // 마지막 값 처리
    if (temp_idx > 0 && val_idx < 5) {
    	Cmd_values[val_idx++] = atoi(temp);
    }
}




//=================================FAN===================================================
//fan3개
//mode 1 co2 로 인해 환기 시스템
//fan1 = 온도로 인해
#if fan_en

void fan_on(){
	  HAL_GPIO_WritePin(Fan_On_GPIO_Port, Fan_On_Pin, GPIO_PIN_RESET);
	  //printf("Fan_on\r\n");

}

void fan_off(){
	  HAL_GPIO_WritePin(Fan_On_GPIO_Port, Fan_On_Pin, GPIO_PIN_SET);
	  //printf("Fan_off\r\n");

}

#endif


//==================================water pump
// A 모터 제어 (PC9, PC8)
//워터 펌프?
//A-1A	PC9
//A-1B	PC8
//B-1A	PC5
//B-1B	PC6






#if water_pump_en

void Water_P1_Start() {
	HAL_GPIO_WritePin(Water_P1_GPIO_Port, Water_P1_Pin, GPIO_PIN_RESET);
//	printf("Water pump1 start\r\n");
}
void Water_P2_Start() {
	HAL_GPIO_WritePin(Water_P2_GPIO_Port, Water_P2_Pin, GPIO_PIN_RESET);
	//printf("Water pump2 Start\r\n");
}

void Water_P1_Stop() {
	HAL_GPIO_WritePin(Water_P1_GPIO_Port, Water_P1_Pin, GPIO_PIN_SET);
	//printf("Water pump1 stop\r\n");
}
void Water_P2_Stop() {
	HAL_GPIO_WritePin(Water_P2_GPIO_Port, Water_P2_Pin, GPIO_PIN_SET);
	//printf("Water pump2 Stop\r\n");
}

#endif


#if light_en
//void light_on(){
//	HAL_GPIO_WritePin(led1_GPIO_Port, led1_Pin,GPIO_PIN_RESET );
//	printf("led on\r\n");
//}
//void light_off(){
//	HAL_GPIO_WritePin(led1_GPIO_Port, led1_Pin,GPIO_PIN_SET );
//	printf("led off\r\n");
//}
void light_on(uint16_t num){
	uint16_t Pwm = map(num, 0, 4095, 4095, 0);
	HAL_GPIO_WritePin(led2_GPIO_Port, led2_Pin, GPIO_PIN_SET);
	TIM11 -> CCR1 = num;


}


void test_led_mode(){
	printf("Test led mode \r\n");
	for(uint16_t i = 0; i<= 4095;)
	{

		HAL_GPIO_WritePin(led2_GPIO_Port, led2_Pin, GPIO_PIN_SET);
		TIM11 -> CCR1 = i;
		i+= 100;
		HAL_Delay(50);
	}

}

uint16_t map(uint16_t value, uint16_t in_min, uint16_t in_max, uint16_t out_min, uint16_t out_max) {
    return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}
//
//void light_on(){
//	HAL_GPIO_WritePin(led1_GPIO_Port, led1_Pin,GPIO_PIN_SET );
//	HAL_GPIO_WritePin(led2_GPIO_Port, led2_Pin,GPIO_PIN_RESET );
//	//__HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, 30000);
//	for(int i = 0 ; i <60000; i=i+10){
//		__HAL_TIM_SET_COMPARE(&htim1, TIM_CHANNEL_1, i);
//		delay(100);
//	}
//	printf("led off\r\n");
//}
//void light_1(){
//	HAL_GPIO_WritePin(led1_GPIO_Port, led1_Pin,GPIO_PIN_SET );
//	HAL_GPIO_WritePin(led2_GPIO_Port, led2_Pin,GPIO_PIN_SET );
//	printf("led off\r\n");
//}
#endif

//


//제어 명령어 -  팬+팰티어, led. 팬, 모터 센서(급수)
void process_commands(int* Cmd_values) {
	int fan_flag = 0;

    for (int i = 0; i < 4; i++) {
        switch (i) {
            case 0: // 온도 관련

                if (Cmd_values[i]==0) {
                	Peltier_Heating();

                }
                else if(Cmd_values[i]==1) {
                	Peltier_Normal();
                }
                else if(Cmd_values[i]==2) {
                    Peltier_Cooling();
                }
                break;
            case 1: // 습도 관련
            	if (Cmd_values[i]==0) {
                	fan_flag = 1;
                }
            	else if(Cmd_values[i]==1) {
                	fan_off();
                }
            	else if(Cmd_values[i]==2) {
                	fan_off();
                }
                break;
            case 2: // Light 관련
            	light_on(Cmd_values[i]);
                break;

            case 3: // CO2 관련
            	if (Cmd_values[i]==0) {
                	fan_flag = 1;
                }
            	else if(Cmd_values[i]==1) {
                	fan_off();
                }
            	else if(Cmd_values[i]==2) {
                	fan_off();
                }
                break;
        }
    }
    if(fan_flag == 1){
    	fan_on();
    }

}

extern uint8_t door_flg;
void manual_process(int* Cmd_values){
	int fan_flag = 0;

	//급수
		if (Cmd_values[1]==0){
			if(Cmd_values[2]==0){

				Water_P1_Start();
			}
			else{
				Water_P1_Stop();
			}
		}
		//배수
		else if (Cmd_values[1]==1){
			if(Cmd_values[2]==0){
				Water_P2_Stop();
			}
			else
			{
				Water_P2_Start();
			}
		}
		//팰티어
		else if (Cmd_values[1]==2){
			if(Cmd_values[2]==0){
				printf("Heating Mode(Mamual Control\r\n)");
				Peltier_Heating();
			}
			else if(Cmd_values[2]==1){
				printf("Normal Mode(Mamual Control\r\n)");
				Peltier_Normal();

			}
			else{
				printf("Cooling Mode(Mamual Control\r\n)");
				Peltier_Cooling();
			}
		}
		//led


		else if (Cmd_values[1]==3){

		}
		//환기팬
		else if (Cmd_values[1]==4){
			if(Cmd_values[2]==0){
				printf("Fan Off(Mamual Control\r\n)");
				fan_off();
			}
			else{
				fan_on();
				printf("Fan On(Mamual Control\r\n)");
			}
		}
		//문
		else if(Cmd_values[1] == 5){
			if(Cmd_values[2]==0){
				door_flg = 2;

			}
			else{
				door_flg = 1;

			}

		}



}
//펠티어 소자

#if pelt_en
void Peltier_Cooling()
{
	//printf("Cooling Mode\r\n");
	HAL_GPIO_WritePin(Peltier1_GPIO_Port, Peltier1_Pin, GPIO_PIN_SET);   // IN1 = HIGH
	HAL_GPIO_WritePin(Peltier2_GPIO_Port, Peltier2_Pin, GPIO_PIN_RESET); // IN2 = LOW
	HAL_GPIO_WritePin(Fan_Peltier1_GPIO_Port, Fan_Peltier1_Pin, GPIO_PIN_SET);


}

// 난방 모드
void Peltier_Heating()
{
	//printf("Heating Mode\r\n");
	HAL_GPIO_WritePin(Peltier1_GPIO_Port, Peltier1_Pin, GPIO_PIN_RESET);
	HAL_GPIO_WritePin(Peltier2_GPIO_Port, Peltier2_Pin, GPIO_PIN_SET);
	HAL_GPIO_WritePin(Fan_Peltier1_GPIO_Port, Fan_Peltier1_Pin, GPIO_PIN_SET);

}

void Peltier_Normal()
{
	//printf("Normal Mode\r\n");
	HAL_GPIO_WritePin(Peltier1_GPIO_Port, Peltier1_Pin, GPIO_PIN_RESET);
	HAL_GPIO_WritePin(Peltier1_GPIO_Port, Peltier1_Pin, GPIO_PIN_RESET);
	HAL_GPIO_WritePin(Fan_Peltier1_GPIO_Port, Fan_Peltier1_Pin, GPIO_PIN_RESET);

}
#endif
//

//

//void delay_us(uint16_t us)
//{
//    __HAL_TIM_SET_COUNTER(&htim1, 0);  // 카운터 초기화
//    while (__HAL_TIM_GET_COUNTER(&htim1) < us);  // 지정 시간까지 대기
//}

//uint32_t read_distance()
//{
//    uint32_t local_time = 0;
//
//    // TRIG 핀 LOW로 초기화
//    HAL_GPIO_WritePin(Trig_GPIO_Port, Trig_Pin,0);
//    delay_us(2);
//    printf("1\r\n");
//
//    // TRIG 핀 HIGH → 10μs 이상
//    HAL_GPIO_WritePin(Trig_GPIO_Port, Trig_Pin, 1);
//    delay_us(1);
//    printf("2\r\n");
//    HAL_GPIO_WritePin(Trig_GPIO_Port, Trig_Pin, 0);
//    printf("3\r\n");
//    printf("%d\r\n",HAL_GPIO_ReadPin(Echo_GPIO_Port, Echo_Pin));
//    // ECHO 핀이 HIGH가 될 때까지 대기
//    while (HAL_GPIO_ReadPin(Echo_GPIO_Port, Echo_Pin) == 0){
//    	printf("wait \r\n");
//    	delay_us(1);
//    }
//
//    printf("%d\r\n",HAL_GPIO_ReadPin(Echo_GPIO_Port, Echo_Pin));
//    // ECHO 핀이 HIGH일 때 시간 측정 시작
//    while (HAL_GPIO_ReadPin(Echo_GPIO_Port, Echo_Pin) == 1)
//    {
//
//    	printf("5\r\n");
//        local_time++;
//        delay_us(1); // 1μs씩 증가
//    }
//
//    // 거리 계산 (cm 단위)
//    // 현실 거리로 *2
//    return local_time / 58 * 2;
//}


void door_open(){
	HAL_GPIO_WritePin(door1_GPIO_Port, door1_Pin, 0);
	HAL_GPIO_WritePin(door2_GPIO_Port, door2_Pin, 1);
	HAL_Delay(1000);
    printf("door open(Manual Control)\r\n");
}

void door_close(){
	HAL_Delay(3000);
	HAL_GPIO_WritePin(door1_GPIO_Port, door1_Pin, 1);
	HAL_GPIO_WritePin(door2_GPIO_Port, door2_Pin, 0);
	HAL_Delay(600);
    printf("door close(Manual Control)\r\n");
}

void door_stop(){
	HAL_GPIO_WritePin(door1_GPIO_Port, door1_Pin, 0);
	HAL_GPIO_WritePin(door2_GPIO_Port, door2_Pin, 0);
    //printf("door stop\r\n");
}


// 			상황(밖) 1 door_flag = 0  	=> 측정된 상태	-> 측정 x
// 			상황(밖) 2 door_flag = 1  	=> 측정  x 	-> 측정 된 상태 	=> 열리는 상태
// 			상황(밖) 3 door_flag = 11 	=> 측정된 상태 -> 측정 된 상태 	=> 멈추는 상태
// 			상황(안) 4 door_flag = 2	=> 측정된 상태	-> 측정 x  		-> 멈춘 상태
// 			상황(안) 5 door_flag = 22	=> 측정 x 	-> 측정 x			=> 멈추는 상태
// 			상황(밖) 6 door_flag = 3	=> 측정 x		-> 측정 된 상태	=> 닫히는 상태
// 			상황(밖) 7 door_flag = 33 	=> 측정 된 상태-> 측정 된 상태	=> 멈춘 (초기 상태)

uint8_t update_door_state(uint8_t door_flag, bool detected)
{
    if (detected) {
        switch (door_flag) {
            case 0:  return 1;
            case 1:  return 11;
            case 11: return 11;
            case 2:  return 3;
            case 22: return 3;
            case 3:  return 33;
            case 33: return 33;
        }
    } else {
        switch (door_flag) {
            case 0:  return 0;
            case 1:
            case 11: return 2;
            case 2:  return 22;
            case 22: return 22;
            case 3:
            case 33: return 0;
        }
    }

    return door_flag;
}
void handle_door_action(uint8_t door_flag)
{
    switch (door_flag) {
        case 0:
        case 11:
        case 2:
        case 22:
        case 33:
            door_stop();
            break;

        case 1:
            door_open();

            door_stop();
            break;

        case 3:
            door_close();
            door_stop();
            break;
    }
}
