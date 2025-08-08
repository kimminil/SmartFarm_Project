

// My Uart lib
// 송 명 규
// 010-2402-4398
// End Ver = V4.6
// Ver1.0 = 2018, 07, 09
// Ver2.0 = 2019, 05, 19
// Ver3.0 = 2020, 11, 06
// ver3.2 = 2022, 11, 28
// ver3.4 = 2022, 12, 23 = LIB 정리
// Ver3.5 = 2023, 06, 16 = 조건식 빌드항목 추가
// Ver4.0 = 2023, 06, 20 = tx func, 콜백함수 추가
// Ver4.1 = 2023, 07, 01 = 콘솔 체널 자동설정 추가, DMA/IRQ 자동설정 추가
// Ver4.2 = 2023, 07, 07 = 변수추가, 함수 수정
// Ver4.3 = 2023, 07, 19 = __PUTCHAR 추가, IRQ Func 정리
// Ver4.4 = 2023, 09. 12 = my_printf함수 변경 = UART채널 선택 멤버변수 추가
// Ver4.5 = 2023, 10. 05 = rx_ok_flag, rx_ready_flag 변수 추가
// Ver4.6 = 2024, 01. 01 = 파일명 변경, RX IRQ Callback 함수 수정
// Ver4.7 = 2024, 03, 10 = RS-485용 tx_str_485 함수 추가, 구조체 포인터 추가
// Ver4.8 = 2025, 04, 16 = FREERTOS 추가 및 IDLE Interrupt CallBack 함수 추가

//==================================================================
/*
 // My uart LIB 사용시 선언 예
#include "My_LIB\my_gpio_lib_v3_2.h"

#define My_Uart_LIB_EN   1
#define Console_Ch2      2
#define USART_Ch_1_EN    1
#define USART_Ch_2_EN    2
#define USART_Ch_3_EN    2
#define IRQ_EN_Uart_1    1
#define IRQ_EN_Uart_2    2
#define IRQ_EN_Uart_3    3
#include "My_LIB\my_uart_lib_v4_3.h"
*/

#ifndef __my_uart_lib__
#define __my_uart_lib__

#ifdef My_Uart_LIB_EN
  #define Uart_Ch_1	1
  #define Uart_Ch_2	2
  #define Uart_Ch_3	3
  #define Uart_Ch_4	4  // L152
  #define Uart_Ch_5	5  // L152
  #define Uart_Ch_6	6  // F746
  #define _CR_	0x0d  //13
  #define _LF_	0x0a  //10

  #include <stdio.h>  // printf, sprintf 사용하기 위해서
  #include <stdarg.h>
  #include <string.h>
  #include "main.h"
  #include "usart.h"

  void vprint(uint8_t ch, const char *fmt, va_list argp);
  void my_printf(uint8_t ch, const char *fmt, ...); // custom printf() function
  void tx_send(uint8_t tx_data, uint8_t ch);
  void tx_str(uint8_t  *tx_d, char ch);        // v3.5
  void tx(uint8_t *tx_d, char ch, char lans); // v3.5

  HAL_StatusTypeDef RcvStat;
  uint8_t usart_ch = 2;  // Nrcleo default usart ch = 2

  // 2022, 9 추가 = 수신 인터럽트가 2번식 걸리는 현상이 있음 = STM32L152
  volatile uint8_t uart_1_irq_cnt = 0;
  volatile uint8_t uart_2_irq_cnt = 0;
  volatile uint8_t uart_3_irq_cnt = 0;
  volatile uint8_t uart_4_irq_cnt = 0;
  volatile uint8_t uart_5_irq_cnt = 0;
  volatile uint8_t uart_6_irq_cnt = 0;
#endif

#if NO_RTOS  // 변수 선언부분은 차후에 통합예정
  struct RX_DATA
   {
    volatile uint8_t Rx_data_1[20];  // uart 1 rx_buf
    volatile uint8_t Rx_data_2[20];  // uart 2 rx_buf
    volatile uint8_t Rx_data_3[20];  // uart 3 rx_buf
    volatile uint8_t Rx_data_4[20];  // uart 3 rx_buf
    volatile uint8_t Rx_data_5[20];  // uart 3 rx_buf
    volatile uint8_t Rx_data_6[20];  // 2023, 8, 6 inc
    volatile uint16_t buff_size;
   }Rx_Data = {0,0,0,0,0,0, 10};
  struct RX_DATA *rx_d = &Rx_Data;

  struct RX_CNT
   {
	volatile uint8_t rx_cnt_1;    // uart 1 수신 Data Counter
	volatile uint8_t rx_cnt_2;    // uart 2 수신 Data Counter
	volatile uint8_t rx_cnt_3;    // uart 3 수신 Data Counter
	volatile uint8_t rx_cnt_4;    // uart 4 수신 Data Counter
	volatile uint8_t rx_cnt_5;    // uart 5 수신 Data Counter
	volatile uint8_t rx_cnt_6;    // 2023, 8, 6 inc
   }Rx_Cnt = {0,0,0,0,0,0};
  struct RX_CNT *rx_cnt = &Rx_Cnt;

  struct RX_FLAG
  {
   volatile uint8_t rx_end_flag_1; // uart1 rx end flag
   volatile uint8_t rx_end_flag_2; // uart2 rx end flag
   volatile uint8_t rx_end_flag_3; // uart3 rx end flag
   volatile uint8_t rx_end_flag_4; // uart4 rx end flag
   volatile uint8_t rx_end_flag_5; // uart5 rx end flag
   volatile uint8_t rx_end_flag_6; // 2023, 8, 6 inc
   volatile int8_t rx_ok_flag;
   volatile int8_t rx_ready_flag;
  }Rx_Flag = {0,0,0,0,0,0,0,0};
  struct RX_FLAG *rx_flag = &Rx_Flag;

#elif RTOS // 변수 선언부분은 차후에 통합예정
  // RX data Save
  volatile uint8_t rx_buf_1[20]= ""; // uart 1 rx_buf
  volatile uint8_t rx_buf_2[20]= ""; // uart 2 rx_buf
  volatile uint8_t rx_buf_3[20]= ""; // uart 3 rx_buf
  volatile uint8_t rx_buf_4[20]= ""; // uart 4 rx_buf
  volatile uint8_t rx_buf_5[20]= ""; // uart 5 rx_buf
  volatile uint8_t rx_buf_6[20]= ""; // uart 6 rx_buf

  // // uart 수신 Data Counter
  volatile uint8_t rx_cnt_1 = 0;    // uart 1 수신 Data Counter
  volatile uint8_t rx_cnt_2 = 0;    // uart 2 수신 Data Counter
  volatile uint8_t rx_cnt_3 = 0;    // uart 3 수신 Data Counter
  volatile uint8_t rx_cnt_4 = 0;    // uart 4 수신 Data Counter
  volatile uint8_t rx_cnt_5 = 0;    // uart 5 수신 Data Counter
  volatile uint8_t rx_cnt_6 = 0;    // uart 6 수신 Data Counter

  // rx end flag
  volatile uint8_t rx_end_flag_1 = 0; // uart 1 rx end flag
  volatile uint8_t rx_end_flag_2 = 0; // uart 2 rx end flag
  volatile uint8_t rx_end_flag_3 = 0; // uart 3 rx end flag
  volatile uint8_t rx_end_flag_4 = 0; // uart 4 rx end flag
  volatile uint8_t rx_end_flag_5 = 0; // uart 5 rx end flag
  volatile uint8_t rx_end_flag_6 = 0; // uart 6 rx end flag
#endif

// 2022, 11, 06 추가 = 교육생들이 좀 더 쉽게하기 위해서 추가 함 = 송신 함수
// 2023, 07, 01 추가 = 콘솔채널 자동설정 추가
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

// printf 사용하기 위해서 = 2023, 06, 23 위치이동
// 2023, 07, 01 추가 = 콘솔채널 자동설정 추가
extern int fputc(int ch, FILE *f)
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
#endif

    __NOP();

   return(ch);
 }

// 2022, 11, 06 추가 = 교육생들이 좀 더 쉽게하기 위해서 추가 함 = 송신
extern int _write(int file, char *ptr, int len)
{
    int DataIdx;
    for (DataIdx = 0; DataIdx < len; DataIdx++)
    {
      // 콘솔에 출력할 수 있도록 하기 위해서 수정 함
      __io_putchar(*ptr++);// == org

      asm("nop");
    }
    return len;
}

// 2022, 11, 06 추가 = 교육생들이 좀 더 쉽게하기 위해서 추가 함 = 송신
extern int __io_getchar(void)
{
    char data[4];
    uint8_t ch, len = 1;

    // 2023, 07, 01 추가 = 콘솔채널 자동설정 추가
#if Console_Ch1
    //UART_HandleTypeDef huart1;
    while(HAL_UART_Receive(&huart1, &ch, 1, 10) != HAL_OK){ }

#elif Console_Ch2
    //UART_HandleTypeDef huart2;
    while(HAL_UART_Receive(&huart2, &ch, 1, 10) != HAL_OK){ }

#elif Console_Ch3
    //UART_HandleTypeDef huart3;
    while(HAL_UART_Receive(&huart3, &ch, 1, 10) != HAL_OK){ }
#endif

    memset(data, 0x00, 4);
    switch(ch)
    {
        case '\r':
        case '\n':
            len = 2;
            sprintf(data, "\r\n");
            break;

        case '\b':
        case 0x7F:
            len = 3;
            sprintf(data, "\b \b");
            break;

        default:
            data[0] = ch;
            break;
    }

    asm("nop");
    return ch;
}

// 2023, 7, 19 추가
#ifdef __GNUC_C__
  #define PUTCHAR_PROTOTYPE int __io_putchar(int ch)
#elif __GNU_F__
  #define PUTCHAR_PROTOTYPE int fputc(int ch, FILE *f)

PUTCHAR_PROTOTYPE
{
    HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, 100);
    return ch;
}
#endif /* __GNUC__ */

// my usart LIB func == 2023, 06, 20 추가
void tx_send(uint8_t tx_data, uint8_t ch)
{
 switch(ch)
  {
   case 1:
           #ifdef USART_Ch_1_EN
	          HAL_UART_Transmit(&huart1, (uint8_t *)&tx_data, 1,10);
            #endif
	     break;

   case 2: // uart 2
           #ifdef USART_Ch_2_EN
             HAL_UART_Transmit(&huart2, (uint8_t *)&tx_data, 1,10);
           #endif
         break;

   case 3: // uart 3
           #ifdef USART_Ch_3_EN
            HAL_UART_Transmit(&huart3, (uint8_t *)&tx_data, 1,10);
           #endif
         break;

   case 4: // uart 4
          #ifdef USART_Ch_4_EN
           HAL_UART_Transmit(&huart4, (uint8_t *)&tx_data, 1, 10);
          #endif
     break;

   case 5: // uart 5
             #ifdef USART_Ch_5_EN
              HAL_UART_Transmit(&huart5, (uint8_t *)&tx_data, 1, 10);
             #endif
        break;

   case 6: // uart 6
                #ifdef USART_Ch_6_EN
                 HAL_UART_Transmit(&huart6, (uint8_t *)&tx_data, 1, 10);
                #endif
           break;

  }
}

// v3.5 == 2023, 06, 18 수정
void tx_str(uint8_t  *tx_d, char ch)
{
  while(*tx_d != '\0')
  {
    tx_send(*tx_d, ch);
    tx_d++;
  }
}

// v3.5 == 2023, 06, 18 추가
// low data tx
void tx(uint8_t *tx_d, char ch, char lans)
{
	 do{
	      tx_send(*tx_d, ch);
	      tx_d++;
	      lans--;
	     }while(lans != 0);
}


// 2023, 06, 20 수정
// 2023, 9, 12 수정 = 멤버변수 추가 = Ver4.4
void vprint(uint8_t ch, const char *fmt, va_list argp)
{
    char string[200];
    if(0 < vsprintf(string,fmt,argp)) // build string
    {
      // 2022, 11, 28수정 = Ver 3.2
     #ifdef USART_Ch_1_EN
     	if(ch == Uart_Ch_1) HAL_UART_Transmit(&huart1, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_2_EN
     	if(ch == Uart_Ch_2) HAL_UART_Transmit(&huart2, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_3_EN
     	if(ch == Uart_Ch_3) HAL_UART_Transmit(&huart3, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_4_EN
     	if(ch == Uart_Ch_4) HAL_UART_Transmit(&huart4, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_5_EN
   	    if(ch == Uart_Ch_5) HAL_UART_Transmit(&huart5, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif

     #ifdef USART_Ch_6_EN
  	    if(ch == Uart_Ch_6) HAL_UART_Transmit(&huart6, (uint8_t*)string, strlen(string), 0xffffff); // send message via UART
     #endif
    }
}

// 2023, 9, 12 수정 = 멤버변수 추가 = Ver4.4
void my_printf(uint8_t ch, const char *fmt, ...) // custom printf() function
{
  va_list argp;
  va_start(argp, fmt);
  vprint(ch, fmt, argp); // 2023, 9, 12 수정 = 멤버변수 추가 = Ver4.4
  va_end(argp);
}

//=======  interrupt call back func  ======================

#if NO_RTOS  // 2025, 04, 16추가
// 2023, 06, 20 추가
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{

#if USART_Ch_1_EN
	// uart1 IRQ
	  if(huart->Instance == USART1)
	   {
		 //---------------------------------------------------------
	     // app user code
		  rx_flag -> rx_end_flag_1 = 1;




	     //My_UART_1_Irq();
		 //printf("UART1 TX = %s\r\n", Rx_data_1);

		 //---------------------------------------------------------
		 __HAL_UART_CLEAR_PEFLAG(&huart1);

		  #if DMA_EN_Uart_1
		      HAL_UART_Receive_DMA(&huart1, (uint8_t *)Rx_data_1, 5);
		  #elif IRQ_EN_Uart_1
		      HAL_UART_Receive_IT(&huart1, (uint8_t *)rx_d -> Rx_data_1, 1);
		  #endif
	   }
#endif

#if USART_Ch_2_EN  // uart 2
  // uart2 IRQ
  if(huart->Instance == USART2)
   {
	 //---------------------------------------------------------
     // app user code
   	 // loop back test

	 rx_flag -> rx_end_flag_2 = 1;
	// rx_cnt -> rx_cnt_2++;

	 //---------------------------------------------------------
	  __HAL_UART_CLEAR_PEFLAG(&huart2);

	  #if DMA_EN_Uart_2
	      HAL_UART_Receive_DMA(&huart2, (uint8_t *)rx_d -> Rx_data_2, 10); //rx_d -> buff_size);
	  #elif IRQ_EN_Uart_2
	      HAL_UART_Receive_IT(&huart2, (uint8_t *)rx_d -> Rx_data_2, 10); //rx_d -> buff_size);
	  #endif
   }
#endif

#if USART_Ch_3_EN
  // uart3 IRQ
  if(huart->Instance == USART3)
   {
  	//---------------------------------------------------------
  	// app user code
	tx_send(Rx_data_3[0], 1);

  	//My_UART_3_Irq();

  	//---------------------------------------------------------
  	__HAL_UART_CLEAR_PEFLAG(&huart3);

  	#if DMA_EN_Uart_3
  	    HAL_UART_Receive_DMA(&huart3, (uint8_t *)Rx_data_3, 20);
  	#elif IRQ_EN_Uart_3
  	    HAL_UART_Receive_IT(&huart3, (uint8_t *)Rx_data_3, 1);
  	#endif
  }
#endif

#if USART_Ch_4_EN
  // uart4 IRQ
   if(huart->Instance == UART4)
    {
   	  //---------------------------------------------------------
   	  // app user code

	   rx_flag -> rx_end_flag_4 = 1;
   	 //---------------------------------------------------------
   	 __HAL_UART_CLEAR_PEFLAG(&huart4);

   	#if DMA_EN_Uart_4
   	    HAL_UART_Receive_DMA(&huart4, (uint8_t *)Rx_data_4, 1);
   	#elif IRQ_EN_Uart_4
   	    HAL_UART_Receive_IT(&huart4, (uint8_t *)rx_d -> Rx_data_4, 17);
   	#endif
   }
#endif

#if USART_Ch_5_EN
   // uart5 IRQ
   if(huart->Instance == USART5)
    {
      //---------------------------------------------------------
      // app user code
      My_UART_5_Irq();

      //---------------------------------------------------------
      __HAL_UART_CLEAR_PEFLAG(&huart5);

      #if DMA_EN_Uart_5
    	  HAL_UART_Receive_DMA(&huart5, (uint8_t *)Rx_data_5, 20);
      #elif IRQ_EN_Uart_5
    	  HAL_UART_Receive_IT(&huart5, (uint8_t *)Rx_data_5, 10);
      #endif
    }
#endif

#if USART_Ch_6_EN
   // uart5 IRQ
   if(huart->Instance == USART6)
    {
      //---------------------------------------------------------
      // app user code


      //---------------------------------------------------------
      __HAL_UART_CLEAR_PEFLAG(&huart6);

      #if DMA_EN_Uart_6
    	  HAL_UART_Receive_DMA(&huart6, (uint8_t *)rx_d -> Rx_data_6, 20);
      #elif IRQ_EN_Uart_6
    	  HAL_UART_Receive_IT(&huart6, (uint8_t *)rx_d -> Rx_data_6, 5);
      #endif
    }
#endif
} // HAL_UART_RxCpltCallback func end
//--------------------------------------------------------------------------

// 2025, 04, 23 추가 = IDLE Call Back Func
void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size)
{
 if(huart->Instance == USART3)
 {
  // rx_d -> RxDataLen = Size;
   rx_flag -> rx_end_flag_3 = 1;

   //echo out == uart2
   //printf("Rx IDLE = %s, %d\r\n", rx_d -> Rx_data_3, rx_d -> RxDataLen);

   // ReLoad
   #if IDLE_DMA_Ch3 // dma == 2024, 04, 23
      HAL_UARTEx_ReceiveToIdle_DMA(&huart3, (uint8_t *)&rx_d -> Rx_data_3, 100);//rx_d -> Rx_buff_size); // 50 Byte rx
   #elif IDLE_IRQ_Ch3 // Interrupt == 2024, 04, 23
      HAL_UARTEx_ReceiveToIdle_IT(&huart3, (uint8_t *)&rx_d -> Rx_data_3, 100); // 50 Byte rx
   #endif
 }
}
#endif

#endif


/*
//===========================================================================================
//  IDLE Interrupt 사용 예제
#if IDLE_DMA_Ch3 // dma == 2024, 04, 23
     HAL_UARTEx_ReceiveToIdle_DMA(&huart3, (uint8_t *)&rx_d -> Rx_data_3, 100);//rx_d -> Rx_buff_size); // 50 Byte rx
  #elif IDLE_IRQ_Ch3 // Interrupt == 2024, 04, 23
     HAL_UARTEx_ReceiveToIdle_IT(&huart3, (uint8_t *)&rx_d -> Rx_data_3, 100); // 50 Byte rx
  #else // == 2024, 04, 23
     HAL_UART_Receive_IT(&huart3, (uint8_t *)rx_d -> Rx_data_3, 10); //rx_d -> buff_size);
  #endif
*/

