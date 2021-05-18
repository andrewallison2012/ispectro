#include "Wire.h" // library for I2C communication to AD5933
#include <stdio.h>

// AD5933 REGISTER MAP
#define Control_D15_to_D8 0x80                            // Read/write
#define Control_D7_to_D0 0x81                             // Read/write
#define Start_frequency_D23_to_D16 0x82                   // Read/write
#define Start_frequency_D15_to_D8 0x83                    // Read/write
#define Start_frequency_D7_to_D0 0x84                     // Read/write
#define Frequency_increment_D23_to_D16 0x85               // Read/write
#define Frequency_increment_D15_to_D8 0x86                // Read/write
#define Frequency_increment_D7_to_D0 0x87                 // Read/write
#define Number_of_increments_D15_to_D8 0x88               // Read/write
#define Number_of_increments_D7_to_D0 0x89                // Read/write
#define Number_of_settling_time_cycles_D15_to_D8 0x8A     // Read/write
#define Number_of_settling_time_cycles_D7_to_D0 0x8B      // Read/write
#define Status_D7_to_D0 0x8F                              // Read only
#define Temperature_data_D15_to_D8 0x92                   // Read only
#define Temperature_data_D7_to_D0 0x93                    // Read only
#define Real_data_D15_to_D8 0x94                          // Read only
#define Real_data_D7_to_D0 0x95                           // Read only
#define Imaginary_data_D15_to_D8 0x96                     // Read only
#define Imaginary_data_D7_to_D0 0x97                      // Read only

#define Slave_Address 0x0D
#define Address_Pointer 0xB0

// Global Variables
const char prefixDelimiter = '<';
const char suffixDelimiter = '>';

boolean readingBuffer = false;
boolean newInput = false;

const byte bufferSize = 40;
char inputBuffer[bufferSize];
byte bytesReceived = 0;
int PGA_BIN = 0b1;

char charactersFromPC[bufferSize] = {0};
int passedInt = 0;
float passedFloat = 0.0;

int globalFlashDelayMs = 1000;
boolean stateVar = true;
byte incomingByte;

short re;
short img;

double kfreq;
double mag;
double phase;
double phasei;
double phasex;
double phasey;
double gain;
double impedance;
double sys_phase;

int scanNumberAtFrequency = 1;
int i=0;
int gf=1;

double sweepUnderWay = 0.0;

double x;
double y;

double xcal;
double ycal;
double xccal;
double yccal;

double t;

const float external_clock = 16000000.0; // 16 Mhz external clock frequency
float Start_Frequency = 1000.0; // 1kHz starting frequency
float Increment_Frequency = 1000.0; // 1kHz step size
int Number_of_Increments = 99; // 99 steps
int Sweep_delay = 333;

boolean AD8130_STATE = true;


int ADG1608_RC_STATE = 0;
int ADG1608_RC_STATE2 = 2;
int ADG1608_RC_STATE3 = 3;

char ADG774_STATE = 'A';
char ADG774_STATE2 = 'A';
char ADG774_STATE3 = 'A';

int ADG1608_GAIN_STATE = 1;
int ADG1608_RFB_STATE = 1;


int PGA_STATE = 1;
int VOLTAGE_STATE = 1;
int VOLTAGE_BIN = 0;
int read_data = 0b0;

int flash_delay = 1000;

double f = Start_Frequency;




//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//  MAIN METHODS
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void setup() {
  // put your setup code here, to run once:
  Wire.begin(); // initiate the wire library and join the I2C bus as a master or slave
  Serial.begin(38400); // sets serial data rate in baud 'bits per second'
  atmega2560PinSetup(); // set I/O pins for the atmega2560
  setAD5933();
  setExternalClock(true); // turn on external AD5933 clock
  configAD5933();
  flashLED(3, 250); // flash the front led 3 times with 250ms between flashes, indicating pin setup complete
  delay(500); // wait 500ms for I/O pins to configure
  Serial.println("<Device Ready>"); // writes '<Device Ready>' to usb to tell computer setup is complete
  // Serial.println("--------------------");
  // Serial.println("COMMANDS: <RUN> <STOP> <VARIABLE BELOW,[int],[float]> see below for format");
  // Serial.println("--------------------");
  // Serial.println("<START_FREQUENCY,0,[1000.00-300000.00]> ");
  // Serial.println(Start_Frequency);
  // Serial.println("<INCREMENT_FREQUENCY,0,[0.00-10000.00]> ");
  // Serial.println(Increment_Frequency);
  // Serial.println("<NUMBER_OF_INCREMENTS,[1-300]> ");
  // Serial.println(Number_of_Increments);
  // Serial.println("<AD8130,[1|0]> ");
  // Serial.println(AD8130_STATE);
  // Serial.println("<ADG774,[1|2|0]> ");
  // Serial.println(ADG774_STATE);
  // Serial.println("<ADG1608_RC,[0-8]> ");
  // Serial.println(ADG1608_RC_STATE);
  // Serial.println("<ADG1608_GAIN,[0-8]> ");
  // Serial.println(ADG1608_GAIN_STATE);
  // Serial.println("<ADG1608_RFB,[0-8]> ");
  // Serial.println(ADG1608_RFB_STATE);
  // Serial.println("--------------------");

}

void loop() {
  // put your main code here, to run repeatedly:

  getDataFromUSB(); // detect "<" and ">" parse using "," and store as "< charactersFromPC[bufferSize], passedInt, passedFloat >"
  variableUpdateFuntion();// update variables from serial

}


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//  FUNCTIONS
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void loopFun() {
  while(stateVar){
    // Serial.println("enter anything to stop");
        if (Serial.available() > 0) {
        for(byte n = 0; n < 1; n++){

            break;
         }
      }
    }
  }


// function that calls function based on usb data input
void variableUpdateFuntion() {
  if (strcmp(charactersFromPC,"RUN") == 0) {
    if (newInput) {
          runSweep();
      }
    }
  if (strcmp(charactersFromPC,"STOP") == 0) {
    if (newInput) {
      setAD5933();
        }
      }
  if (strcmp(charactersFromPC,"LEDOFF") == 0) {
    if (newInput) {
      setLED(false);
      // Serial.print("led off");
      // Serial.println();
      }
    }
  if (strcmp(charactersFromPC,"LEDON") == 0) {
    if (newInput) {
      if (newInput)
      setLED(true);
      // Serial.print("led on");
      // Serial.println();
      }
    }
  if (strcmp(charactersFromPC,"FLASH") == 0) {
    if (newInput) {
      flashLED(passedInt, flash_delay);
      // Serial.print("flashing");
      // Serial.println();
      }
    }
  if (strcmp(charactersFromPC,"FLASH_DELAY") == 0) {
    if (newInput) {
      flash_delay = passedInt;
      // Serial.print("delay set to: ");
      // Serial.print(flash_delay);
      // Serial.println();
      }
    }
  if (strcmp(charactersFromPC,"START_FREQUENCY") == 0) {
    if (newInput) {
      Start_Frequency = passedFloat;
      // Serial.print("Start_Frequency set to: ");
      // Serial.print(Start_Frequency);
      // Serial.println();
      }
    }
   if (strcmp(charactersFromPC,"INCREMENT_FREQUENCY") == 0) {
    if (newInput) {
      Increment_Frequency = passedFloat;
      // Serial.print("Increment_Frequency set to: ");
      // Serial.print(Increment_Frequency);
      // Serial.println();
      }
    }

   if (strcmp(charactersFromPC,"NUMBER_OF_INCREMENTS") == 0) {
    if (newInput) {
      Number_of_Increments = passedInt + 1; // corrects for the first step
      // Serial.print("Number_of_Increments set to: ");
      // Serial.print(Number_of_Increments);
      // Serial.println();
      }
    }
   if (strcmp(charactersFromPC,"SWEEP_DELAY") == 0) {
    if (newInput) {
      Sweep_delay = passedInt;
      // Serial.print("Sweep_delay set to: ");
      // Serial.print(Sweep_delay);
      // Serial.println();
      }
    }
   if (strcmp(charactersFromPC,"PGA") == 0) {
    if (newInput) {
      if (passedInt == 0) {
        writeData(Control_D15_to_D8,0b1); // D8 PGA gain; 1 = ×1
        PGA_STATE = 1;
        PGA_BIN = 0b1;
      }
      if (passedInt == 1) {
        writeData(Control_D15_to_D8,0b0); // D8 PGA gain; 0 = ×5
        PGA_STATE = 5;
        PGA_BIN = 0b0;
      }
        // Serial.print("PGA: ");
        // Serial.print(PGA_STATE);
      }
    }
   if (strcmp(charactersFromPC,"VOLTAGE") == 0) {
    if (newInput) {
      if (passedInt == 0) {
        read_data = readData(Control_D15_to_D8);
        writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b1) | 0b000); // 2.0 V p-p
        VOLTAGE_BIN = 0b000;
        VOLTAGE_STATE = 0;
        // Serial.print("readData: ");
        // Serial.println(read_data);
        // Serial.print("writeData: ");
        // Serial.println(VOLTAGE_BIN);
        read_data = readData(Control_D15_to_D8);
        // Serial.print("readData: ");
        // Serial.println(read_data);
      }
      if (passedInt == 1) {
        read_data = readData(Control_D15_to_D8);
        writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b1) | 0b010); // 200 mV p-p
        VOLTAGE_BIN = 0b010;
        VOLTAGE_STATE = 1;
        // Serial.print("readData: ");
        // Serial.println(read_data);
        // Serial.print("writeData: ");
        // Serial.println(VOLTAGE_BIN);
        read_data = readData(Control_D15_to_D8);
        // Serial.print("readData: ");
        // Serial.println(read_data);
      }
      if (passedInt == 2) {
        read_data = readData(Control_D15_to_D8);
        writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b1) | 0b100); // 400 mV p-p
        VOLTAGE_BIN = 0b100;
        VOLTAGE_STATE = 2;
        // Serial.print("readData: ");
        // Serial.println(read_data);
        // Serial.print("writeData: ");
        // Serial.println(VOLTAGE_BIN);
        read_data = readData(Control_D15_to_D8);
        // Serial.print("readData: ");
        // Serial.println(read_data);
      }
      if (passedInt == 3) {
        read_data = readData(Control_D15_to_D8);
        writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b1) | 0b110); // 1.0 V p-p
        VOLTAGE_BIN = 0b110;
        VOLTAGE_STATE = 3;
        // Serial.print("readData: ");
        // Serial.println(read_data);
        // Serial.print("writeData: ");
        // Serial.println(VOLTAGE_BIN);
        read_data = readData(Control_D15_to_D8);
        // Serial.print("readData: ");
        // Serial.println(read_data);
      }
        // Serial.print("VOLTAGE_STATE: ");
        // Serial.println(VOLTAGE_STATE);
      }
    }
   if (strcmp(charactersFromPC,"AD8130") == 0) {
    if (newInput) {
      if (passedInt == 1) {
        AD8130_STATE = true;
      }
      if (passedInt == 0) {
        AD8130_STATE = false;
      }
        AD8130(AD8130_STATE);
        // Serial.print("AD8130: ");
        // Serial.print(AD8130_STATE);
      }
    }
   if (strcmp(charactersFromPC,"ADG774_STATE") == 0) {
    if (newInput) {
      if (passedInt == 1) {
        ADG774_STATE = 'A';
      }
      if (passedInt == 2) {
        ADG774_STATE = 'B';
      }
      if (passedInt == 0) {
        ADG774_STATE = 'Z';
      }
        ADG774(ADG774_STATE);
        // Serial.print("ADG774_STATE: ");
        // Serial.print(ADG774_STATE);
      }
    }
   if (strcmp(charactersFromPC,"ADG774_STATE2") == 0) {
    if (newInput) {
      if (passedInt == 1) {
        ADG774_STATE2 = 'A';
      }
      if (passedInt == 2) {
        ADG774_STATE2 = 'B';
      }
      if (passedInt == 0) {
        ADG774_STATE2 = 'Z';
      }
        ADG774(ADG774_STATE2);
        // Serial.print("ADG774_STATE2: ");
        // Serial.print(ADG774_STATE2);
      }
    }
   if (strcmp(charactersFromPC,"ADG774_STATE3") == 0) {
    if (newInput) {
      if (passedInt == 1) {
        ADG774_STATE3 = 'A';
      }
      if (passedInt == 2) {
        ADG774_STATE3 = 'B';
      }
      if (passedInt == 0) {
        ADG774_STATE3 = 'Z';
      }
        ADG774(ADG774_STATE3);
        // Serial.print("ADG774_STATE3: ");
        // Serial.print(ADG774_STATE3);
      }
    }
   if (strcmp(charactersFromPC,"ADG1608_RC") == 0) {
    if (newInput) {
      ADG1608_RC_STATE = passedInt;
      ADG1608_RC(ADG1608_RC_STATE);
      // Serial.print("ADG1608_RC: ");
      // Serial.print(ADG1608_RC_STATE);
      }
    }
   if (strcmp(charactersFromPC,"ADG1608_RC2") == 0) {
    if (newInput) {
      ADG1608_RC_STATE2 = passedInt;
      // Serial.print("ADG1608_RC2: ");
      // Serial.print(ADG1608_RC_STATE2);
      }
    }
   if (strcmp(charactersFromPC,"ADG1608_RC3") == 0) {
    if (newInput) {
      ADG1608_RC_STATE3 = passedInt;
      // Serial.print("ADG1608_RC3: ");
      // Serial.print(ADG1608_RC_STATE3);
      }
    }
   if (strcmp(charactersFromPC,"ADG1608_GAIN") == 0) {
    if (newInput) {
      ADG1608_GAIN_STATE = passedInt;
      ADG1608_GAIN(ADG1608_GAIN_STATE);
      // Serial.print("ADG1608_GAIN: ");
      // Serial.print(ADG1608_GAIN_STATE);
      }
    }
   if (strcmp(charactersFromPC,"ADG1608_RFB") == 0) {
    if (newInput) {
      ADG1608_RFB_STATE = passedInt;
      ADG1608_RFB(ADG1608_RFB_STATE);
      // Serial.print("ADG1608_RFB: ");
      // Serial.print(ADG1608_RFB_STATE);
      }
    }
    newInput = false;
  }

// update variable function
void updateFlashCount(){
  globalFlashDelayMs = passedInt;

  }


void runSweep() {
  configAD5933();
  LED(true);
  AD8130(AD8130_STATE);
  ADG1608_GAIN(ADG1608_GAIN_STATE);
  ADG1608_RFB(ADG1608_RFB_STATE);
  ADG774(ADG774_STATE); // shifts leads to external lead circuit
  ADG1608_RC(ADG1608_RC_STATE);
  delay(1000);
  delay(Sweep_delay); // wait for 1000 ms
  initializeSweep();

  // run while the Status register says that the sweep is not complete
while((readData(Status_D7_to_D0) & 0x07) < 4 ) { // reads Status Register, to see if D2 is less than 1 (i.e. 0), 0 in at D2 in this register ('Status Register') indicates that the frequency sweep is complete
    int dataAvaliable = readData(Status_D7_to_D0) & 2;  // reads Status Register, uses an and '&' bit wise operator to see if the register is equal to 1 at the D1 bit, this indicates if there is valid real or imaginary data is avaliable

    if (Serial.available() > 0) {
        break;
    }

      //////////////////////////////////////////////////////////////////////// 1
    if (dataAvaliable == 2) { // if dataAvaliable
        if (scanNumberAtFrequency == 1) { // if dataAvaliable
                  readRealandImg();
                  x = (double)re * 1.0;
                  y = (double)img * 1.0;
                  if((readData(Status_D7_to_D0) & 0x07) < 4 ){ // if scan not complete
                    ADG774(ADG774_STATE2);
                    ADG1608_RC(ADG1608_RC_STATE2);
                    delay(Sweep_delay);
                    scanNumberAtFrequency = 2; // i++;
                    writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b111) | 0b1000000); // repeats at current frequency
                    dataAvaliable = readData(Status_D7_to_D0) & 0b10;
                  }

      }
      //////////////////////////////////////////////////////////////////////// 2
      if (dataAvaliable == 2 && scanNumberAtFrequency == 2) {
                  readRealandImg();
                  xccal = (double)re * 1.0;
                  yccal = (double)img * 1.0;
                  if((readData(Status_D7_to_D0) & 0x07) < 4 ){ // if scan not complete
                    ADG774(ADG774_STATE3);
                    ADG1608_RC(ADG1608_RC_STATE3);
                    delay(Sweep_delay); // wait
                    scanNumberAtFrequency = 3; // i++;
                    writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b111) | 0b1000000); // repeats at current frequency
                    dataAvaliable = readData(Status_D7_to_D0) & 0b10;
             }
        }

      //////////////////////////////////////////////////////////////////////// 3
        if (dataAvaliable == 2 && scanNumberAtFrequency == 3) {
                     readRealandImg();
                     xcal = (double)re * 1.0;
                     ycal = (double)img * 1.0;
                     t = measureTemperatureDouble();
                     t = (double)t * 1.0;
                     sendToPC(&f, &x, &y,  &xcal, &ycal, &xccal, &yccal, &t, &sweepUnderWay);
                     ADG774(ADG774_STATE);
                     ADG1608_RC(ADG1608_RC_STATE);
                     delay(Sweep_delay); // wait

                  if((readData(Status_D7_to_D0) & 0x07) < 4 ){ // if scan not complete
                        f = f + Increment_Frequency;
                        writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0x07) | 0x30); // next frequency
                        i++;
                        scanNumberAtFrequency = 1;

                      }
                  }
                  if (f == (Increment_Frequency * float(Number_of_Increments)) + Start_Frequency) {
                    writeData(0x80,(readData(0x80) & 0x07) | 0xA0);
                    }
      }
    } // close while
    endSweep();
} // close runSweep() function


void readRealandImg() {
    byte R1 = readData(Real_data_D15_to_D8);
    byte R2 = readData(Real_data_D7_to_D0);
    re = (R1 << 8) | R2;
    R1  = readData(Imaginary_data_D15_to_D8);
    R2  = readData(Imaginary_data_D7_to_D0);
    img = (R1 << 8) | R2;
}


double measureTemperatureDouble(){
  // Measure temperature '10010000'
  writeData(Control_D15_to_D8, 0x90);
  //TODO: necessary to write to second control register?
  delay(10); // wait for 10 ms
  //Check status reg for temp measurement available
  int flag = readData(Status_D7_to_D0)& 1;
  if (flag == 1) {
    // Temperature is available
    int temperatureData = readData(Temperature_data_D15_to_D8) << 8;
    temperatureData |= readData(Temperature_data_D7_to_D0);
    temperatureData &= 0x3FFF; // remove first two bits
    if (temperatureData & 0x2000 == 1) { // negative temperature
      temperatureData -= 0x4000;
    }
    double val = double(temperatureData) / 32;
    double valZero = double(0.0);
    temperatureData /= 32;
    return val;
  } else {
    double valZero = double(0.0);
    return valZero;
  }
}


// function to save usb data sent by computer into buffer
void getDataFromUSB() {

  if (Serial.available() > 0) { // checks for characters in buffer, Serial.avaliable() checks 64 byte USB recieved buffer - ie data that come from computer - and returns the number of characters

    char bufferCharacter = Serial.read(); // reads incoming serial data and returns first byte of serial data avaliable, returns -1 if no data avaliable

    if(bufferCharacter == suffixDelimiter) { // PARSES AT END IF AT END... if character in buffer is the '>' character stop buffer reading and parse the recieved data
      readingBuffer = false;
      newInput = true;
      inputBuffer[bytesReceived] = 0;
      parseData(); // function that saves buffer data to variables
      }
    if(readingBuffer) { // ADDING CHARACTERS FROM BUFFER... if reading buffer is true... (and no '>' detected from last step)
      inputBuffer[bytesReceived] = bufferCharacter; // then add the bufferCharacter to inputBuffer array at the index of the integer bytesRecieved
      bytesReceived ++; // at one to the bytesRecieved index to store next value if needed
      if(bytesReceived == bufferSize) { // if bytesRecieved (previous interated value) is equal to bufferSize set by global variable (40) then...
        bytesReceived = bufferSize - 1; // subtract 1 from bufferSize (which undoes ++ above, and saves final length/index of string) and save if as the index bytesRecieved, which will be used as inputBuffer array index... used at the end of buffer string
        }
      }
    if(bufferCharacter == prefixDelimiter) { // FINDS START AND STARTS READING... if the bufferCharacter is '<' ...
      bytesReceived = 0; // set bytes recieved to 0
      readingBuffer = true; // set readingBuffer to true ... this makes above if statements evaluate for all characters until '>' is reached
      }
    }
  }

void parseData() {
  char * stringTokenIndex; // stringTokenIndex is not a character but a pointer to an address that holdscharacters (characters)

  stringTokenIndex = strtok(inputBuffer,","); // this copies the characters before the 1st "," and stores them at the stringTokenIndex address
  strcpy(charactersFromPC, stringTokenIndex); // copy value at stringTokenIndex address into charactersFromPC array (which can be used in if functions later on in the code)

  stringTokenIndex = strtok(NULL, ","); // this copies the characters after the 1st "," and stores them at the stringTokenIndex address
  passedInt = atoi(stringTokenIndex); // converts a character sting to an int and stores it in the variable passedInt

  stringTokenIndex = strtok(NULL, ","); // this copies the characters after the 2nd "," and stores them at the stringTokenIndex address
  passedFloat = atof(stringTokenIndex);  // converts a character sting to a float and stores it in the variable passedFloat

  }


// function to flash front led, control the number of flashes and time between flashes
void flashLED(int numberOfFlashes, int waitTimeMs){
  for(byte n = 0; n < numberOfFlashes; n++) {
    digitalWrite(13, LOW); // turn front led indicator led off
    delay(waitTimeMs); // wait time between led on and off
    digitalWrite(13, HIGH); // turn front indicator led on
    delay(waitTimeMs); // wait time between led on and off
    }
    digitalWrite(13, LOW); // turn front led indicator led off
}


// function to turn on and off front led
void setLED(boolean state) {
  switch(state){
    case true:
      digitalWrite(13, HIGH);
      break;
    case false:
      digitalWrite(13, LOW);
      break;
    }
  }


// function to set up IO pins this (this is written for the atmega2560)
void atmega2560PinSetup() {
  // LED
  pinMode(LED_BUILTIN, OUTPUT); // REAR DATA TRANSFER LED
  pinMode(13, OUTPUT); // FRONT ORANGE INDICATOR LED

  // SG-615
  pinMode(49, OUTPUT); // XTAL-EN ENABLES AD5933 EXTERNAL XTAL

  // AD8130
  pinMode(A10, OUTPUT); // PD-AD8130 ENABLE CURRENT SOURCE

  // ADG774
  pinMode(A8, OUTPUT); // CAL_EN ADG774 CALIBRATION OR LEAD SELECTION
  pinMode(A9, OUTPUT); // CAL_IN ADG774 CALIBRATION OR LEAD SELECTION

  // ADG1608-1
  pinMode(30, OUTPUT); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
  pinMode(32, OUTPUT); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
  pinMode(33, OUTPUT); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
  pinMode(34, OUTPUT); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION

  // ADG1608-2
  pinMode(43, OUTPUT); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
  pinMode(45, OUTPUT); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
  pinMode(46, OUTPUT); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
  pinMode(47, OUTPUT); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION

  // ADG1608-3
  pinMode(22, OUTPUT); // IN_AMP_EN ADG1608 RFB SELECTION
  pinMode(24, OUTPUT); // IN_AMP_A0 ADG1608 RFB SELECTION
  pinMode(25, OUTPUT); // IN_AMP_A1 ADG1608 RFB SELECTION
  pinMode(26, OUTPUT); // IN_AMP_A2 ADG1608 RFB SELECTION
  }


// function to enable or disable external AD5933 clock
void setExternalClock(boolean state) {
  switch(state){
    case true: //ENABLE
      digitalWrite(49, HIGH);
      break;
    case false: //DISABLE
      digitalWrite(49, LOW);
      break;
    }
  }

void LED(boolean state){
  switch(state) {
        case true: //LED ON
          digitalWrite(13, HIGH); // FRONT ORANGE INDICATOR LED ON
          break;

        case false:  //LED OFF
          digitalWrite(13, LOW); // FRONT ORANGE INDICATOR LED OFF
          break;
      }
  }


void AD8130(boolean state){
  switch(state) {
        case true:  //ENABLED
          digitalWrite(A10, HIGH); // PD-AD8130 ENABLE CURRENT SOURCE
          break;

        case false:  //DISABLED
          digitalWrite(A10, LOW); // PD-AD8130 DISABLE CURRENT SOURCE
          break;
      }
  }


void ADG774(char route){
    switch(route) {
        case 'A':  //A
          digitalWrite(A8, LOW); // CAL_EN ADG774 CALIBRATION OR LEAD SELECTION
          digitalWrite(A9, LOW); // CAL_IN ADG774 CALIBRATION OR LEAD SELECTION
          break;

        case 'B':  //B
          digitalWrite(A8, LOW); // CAL_EN ADG774 CALIBRATION OR LEAD SELECTION
          digitalWrite(A9, HIGH); // CAL_IN ADG774 CALIBRATION OR LEAD SELECTION
          break;

        case 'Z':  //HIGH IMPEDANCE
          digitalWrite(A8, HIGH); // CAL_EN ADG774 CALIBRATION OR LEAD SELECTION
          digitalWrite(A9, LOW); // CAL_IN ADG774 CALIBRATION OR LEAD SELECTION
          break;
      }
  }


void ADG1608_RC(int route){
    switch(route) {
        case 0:  //DISABLED
          digitalWrite(30, LOW); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, LOW); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, LOW); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, LOW); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;
        case 1:  //S1
          digitalWrite(30, HIGH); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, LOW); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, LOW); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, LOW); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;

        case 2:  //S2
          digitalWrite(30, HIGH); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, HIGH); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, LOW); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, LOW); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;

        case 3:  //S3
          digitalWrite(30, HIGH); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, LOW); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, HIGH); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, LOW); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;

        case 4:  //S4
          digitalWrite(30, HIGH); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, HIGH); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, HIGH); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, LOW); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;

        case 5:  //S5
          digitalWrite(30, HIGH); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, LOW); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, LOW); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, HIGH); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;

        case 6:  //S6
          digitalWrite(30, HIGH); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, HIGH); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, LOW); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, HIGH); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;

        case 7:  //S7
          digitalWrite(30, HIGH); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, LOW); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, HIGH); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, HIGH); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;

        case 8:  //S8
          digitalWrite(30, HIGH); // RESIS_EN ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(32, HIGH); // RESIS_A0 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(33, HIGH); // RESIS_A1 ADG1608 R/RC CALIBRATION SELECTION
          digitalWrite(34, HIGH); // RESIS_A2 ADG1608 R/RC CALIBRATION SELECTION
          break;
      }
  }


void ADG1608_GAIN(int route){
    switch(route) {
        case 0:  //DISABLED
          digitalWrite(43, LOW); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, LOW); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, LOW); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, LOW); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;

        case 1:  //S1
          digitalWrite(43, HIGH); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, LOW); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, LOW); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, LOW); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;

        case 2:  //S2
          digitalWrite(43, HIGH); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, HIGH); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, LOW); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, LOW); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;

        case 3:  //S3
          digitalWrite(43, HIGH); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, LOW); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, HIGH); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, LOW); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;

        case 4:  //S4
          digitalWrite(43, HIGH); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, HIGH); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, HIGH); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, LOW); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;

        case 5:  //S5
          digitalWrite(43, HIGH); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, LOW); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, LOW); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, HIGH); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;

        case 6:  //S6
          digitalWrite(43, HIGH); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, HIGH); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, LOW); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, HIGH); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;

        case 7:  //S7
          digitalWrite(43, HIGH); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, LOW); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, HIGH); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, HIGH); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;

        case 8:  //S8
          digitalWrite(43, HIGH); // RG_EN ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(45, HIGH); // RG_A0 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(46, HIGH); // RG_A1 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          digitalWrite(47, HIGH); // RG_A2 ADG1608 IN-AMP RESISTOR GAIN SELECTION
          break;
      }
  }


void ADG1608_RFB(int route){
    switch(route) {
        case 0:  //DISABLED
          digitalWrite(22, LOW); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, LOW); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, LOW); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, LOW); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;

        case 1:  //S1
          digitalWrite(22, HIGH); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, LOW); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, LOW); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, LOW); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;

        case 2:  //S2
          digitalWrite(22, HIGH); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, HIGH); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, LOW); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, LOW); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;

        case 3:  //S3
          digitalWrite(22, HIGH); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, LOW); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, HIGH); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, LOW); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;

        case 4:  //S4
          digitalWrite(22, HIGH); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, HIGH); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, HIGH); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, LOW); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;

        case 5:  //S5
          digitalWrite(22, HIGH); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, LOW); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, LOW); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, HIGH); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;

        case 6:  //S6
          digitalWrite(22, HIGH); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, HIGH); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, LOW); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, HIGH); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;

        case 7:  //S7
          digitalWrite(22, HIGH); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, LOW); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, HIGH); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, HIGH); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;

        case 8:  //S8
          digitalWrite(22, HIGH); // IN_AMP_EN ADG1608 RFB SELECTION
          digitalWrite(24, HIGH); // IN_AMP_A0 ADG1608 RFB SELECTION
          digitalWrite(25, HIGH); // IN_AMP_A1 ADG1608 RFB SELECTION
          digitalWrite(26, HIGH); // IN_AMP_A2 ADG1608 RFB SELECTION
          break;
      }
  }

void setAD5933() {
  writeData(Control_D15_to_D8,0b0);   //nop - clear ctrl-reg
  writeData(Control_D7_to_D0,0b10000);   //reset ctrl register
  writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0x07) | 0xA0); //Power down
  LED(false);
  AD8130(false); // disable AD8130, constant current source
}


byte Frequency_Code(float start_frequency, int state) {
  long calculated_value = long((start_frequency/(external_clock/4)) * pow(2,27));
  byte code;
   switch (state) {
    case 1:
      code = (calculated_value & 0b111111110000000000000000) >> 0b10000;
      break;
    case 2:
      code = (calculated_value & 0b1111111100000000) >> 0b1000;
      break;
    case 3:
      code = (calculated_value & 0b11111111);
      break;
    default:
      code = 0;
    }
    return code;
  }


void configAD5933() {
  writeData(Control_D15_to_D8, VOLTAGE_STATE);
  writeData(Control_D15_to_D8,PGA_BIN); // D8 PGA gain; 0 = ×5, 1 = ×1
  writeData(Control_D7_to_D0,0b1000); // D3 External system clock; set to 1

  writeData(Start_frequency_D23_to_D16,Frequency_Code(Start_Frequency, 1));
  writeData(Start_frequency_D15_to_D8,Frequency_Code(Start_Frequency, 2));
  writeData(Start_frequency_D7_to_D0,Frequency_Code(Start_Frequency, 3));

  writeData(Frequency_increment_D23_to_D16,Frequency_Code(Increment_Frequency, 1));
  writeData(Frequency_increment_D15_to_D8,Frequency_Code(Increment_Frequency, 2));
  writeData(Frequency_increment_D7_to_D0,Frequency_Code(Increment_Frequency, 3));

  writeData(Number_of_increments_D15_to_D8,(Number_of_Increments & 0b1111100000000) >> 0b1000);
  writeData(Number_of_increments_D7_to_D0,(Number_of_Increments & 0b11111111));

  writeData(Number_of_settling_time_cycles_D15_to_D8,0b111); // D15 to D11 Don’t care, D10 to D9 2-bit decode (1 1 No. of cycles × 4), D8 MSB number of settling time cycles
  writeData(Number_of_settling_time_cycles_D7_to_D0,0b11111111); // D7 to D0 Number of settling time cycles


  }

void initializeSweep() {
  AD8130(true); // enable AD8130, constant current source

  writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b111) | 0b10110000); // standby
  writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b111) | 0b10000); //  initialize 11
  writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0b111) | 0b100000); // start 11
  sweepUnderWay = 1.0;
  f = Start_Frequency;
}

void endSweep() {
  AD8130(false); // disable AD8130, constant current source
  writeData(Control_D15_to_D8,(readData(Control_D15_to_D8) & 0x07) | 0xA0);
  sweepUnderWay = 0.0;
  LED(false);
}



//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//  DATA METHODS
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void writeData(int registerAddress, int data) {
  Wire.beginTransmission(Slave_Address);
  Wire.write(registerAddress);
  Wire.write(data);
  Wire.endTransmission();
  delay(1);
  }

int readData(int registerAddress) {
  int data;
  Wire.beginTransmission(Slave_Address);
  Wire.write(Address_Pointer);
  Wire.write(registerAddress);
  Wire.endTransmission();
  delay(1);

  Wire.requestFrom(Slave_Address,1);
  if (Wire.available() >= 1){
    data = Wire.read();
  }
  else {
    data = -1;
  }
  delay(1);
  return data;
}

void sendToPC(double* data1, double* data2, double* data3, double* data4, double* data5, double* data6, double* data7, double* data8, double* data9) {
  byte* byteData1 = (byte*)(data1);
  byte* byteData2 = (byte*)(data2);
  byte* byteData3 = (byte*)(data3);
  byte* byteData4 = (byte*)(data4);
  byte* byteData5 = (byte*)(data5);
  byte* byteData6 = (byte*)(data6);
  byte* byteData7 = (byte*)(data7);
  byte* byteData8 = (byte*)(data8);
  byte* byteData9 = (byte*)(data9);
  byte buf[36] = {byteData1[0], byteData1[1], byteData1[2], byteData1[3],
                 byteData2[0], byteData2[1], byteData2[2], byteData2[3],
                 byteData3[0], byteData3[1], byteData3[2], byteData3[3],
                 byteData4[0], byteData4[1], byteData4[2], byteData4[3],
                 byteData5[0], byteData5[1], byteData5[2], byteData5[3],
                 byteData6[0], byteData6[1], byteData6[2], byteData6[3],
                 byteData7[0], byteData7[1], byteData7[2], byteData7[3],
                 byteData8[0], byteData8[1], byteData8[2], byteData8[3],
                 byteData9[0], byteData9[1], byteData9[2], byteData9[3]};
  Serial.write(buf, 36);
}


void sendToPC(int* data1, int* data2, int* data3) {
  byte* byteData1 = (byte*)(data1);
  byte* byteData2 = (byte*)(data2);
  byte* byteData3 = (byte*)(data3);
  byte buf[6] = {byteData1[0], byteData1[1],
                 byteData2[0], byteData2[1],
                 byteData3[0], byteData3[1]};
  Serial.write(buf, 6);
}