/**********************************************************************
* Copyright (c) 2006-2010 SmarAct GmbH
*
* File name: SCU3DControl.h
* Author   : Marc Schiffner
* Version  : 1.2
*
* This is the software interface to the SCU product family.
* Please refer to the USB Interface Description document
* for a detailed documentation.
*
* THIS  SOFTWARE, DOCUMENTS, FILES AND INFORMATION ARE PROVIDED 'AS IS'
* WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING,
* BUT  NOT  LIMITED  TO,  THE  IMPLIED  WARRANTIES  OF MERCHANTABILITY,
* FITNESS FOR A PURPOSE, OR THE WARRANTY OF NON-INFRINGEMENT.
* THE  ENTIRE  RISK  ARISING OUT OF USE OR PERFORMANCE OF THIS SOFTWARE
* REMAINS WITH YOU.
* IN  NO  EVENT  SHALL  THE  SMARACT  GMBH  BE  LIABLE  FOR ANY DIRECT,
* INDIRECT, SPECIAL, INCIDENTAL, CONSEQUENTIAL OR OTHER DAMAGES ARISING
* OUT OF THE USE OR INABILITY TO USE THIS SOFTWARE.
**********************************************************************/

#ifndef SCU3DCONTROL_H
#define SCU3DCONRTOL_H

#ifdef SCU3DCONTROL_EXPORTS
#define SCU3DCONTROL_API __declspec(dllexport)
#else
#define SCU3DCONTROL_API __declspec(dllimport)
#endif

typedef unsigned int SA_STATUS;
typedef unsigned int SA_INDEX;
typedef unsigned int SA_PACKET_TYPE;

// defines a data packet for the asynchronous mode
typedef struct SA_packet {
	SA_PACKET_TYPE packetType;					// type of packet (see below)
	SA_INDEX channelIndex;						// source channel
	unsigned int data1;							// data field
	signed int data2;							// data field
	signed int data3;							// data field
} SA_PACKET;

// configuration flags for SA_InitDevices
#define SA_SYNCHRONOUS_COMMUNICATION			0
#define SA_ASYNCHRONOUS_COMMUNICATION			1
#define SA_HARDWARE_RESET						2

// configuration flags for SA_SetReportOnComplete_A
#define SA_NO_REPORT_ON_COMPLETE				0
#define SA_REPORT_ON_COMPLETE					1

// function status return types
#define	SA_OK									0
#define	SA_INITIALIZATION_ERROR					1
#define	SA_NOT_INITIALIZED_ERROR				2
#define	SA_NO_DEVICES_FOUND_ERROR				3
#define	SA_TOO_MANY_DEVICES_ERROR				4
#define	SA_INVALID_DEVICE_INDEX_ERROR			5
#define	SA_INVALID_CHANNEL_INDEX_ERROR			6
#define	SA_TRANSMIT_ERROR						7
#define	SA_WRITE_ERROR							8
#define	SA_INVALID_PARAMETER_ERROR				9
#define	SA_READ_ERROR							10
#define	SA_INTERNAL_ERROR						12
#define SA_WRONG_MODE_ERROR						13
#define SA_PROTOCOL_ERROR						14
#define SA_TIMEOUT_ERROR						15
#define SA_NOTIFICATION_ALREADY_SET_ERROR		16
#define SA_ID_LIST_TOO_SMALL_ERROR				17
#define SA_DEVICE_ALREADY_ADDED_ERROR			18
#define SA_DEVICE_NOT_FOUND_ERROR				19
#define SA_INVALID_COMMAND_ERROR				128
#define SA_COMMAND_NOT_SUPPORTED_ERROR			129
#define SA_NO_SENSOR_PRESENT_ERROR				130
#define SA_WRONG_SENSOR_TYPE_ERROR				131
#define SA_END_STOP_REACHED_ERROR				132
#define SA_COMMAND_OVERRIDDEN_ERROR				133
#define	SA_OTHER_ERROR							255

// packet types (for asynchronous mode)
#define SA_NO_PACKET_TYPE						0
#define SA_ERROR_PACKET_TYPE					1
#define SA_POSITION_PACKET_TYPE					2
#define SA_ANGLE_PACKET_TYPE					3
#define SA_COMPLETED_PACKET_TYPE				4
#define SA_STATUS_PACKET_TYPE					5
#define SA_CLOSED_LOOP_FREQUENCY_PACKET_TYPE	6
#define SA_SENSOR_TYPE_PACKET_TYPE				7
#define SA_SENSOR_PRESENT_PACKET_TYPE			8
#define SA_AMPLITUDE_PACKET_TYPE				9
#define SA_POSITIONER_ALIGNMENT_PACKET_TYPE		10
#define SA_SAFE_DIRECTION_PACKET_TYPE			11
#define SA_INVALID_PACKET_TYPE					255

// channel status codes
#define SA_STOPPED_STATUS						0
#define SA_SETTING_AMPLITUDE_STATUS				1
#define SA_MOVING_STATUS						2
#define SA_TARGETING_STATUS						3
#define SA_HOLDING_STATUS						4
#define SA_CALIBRATING_STATUS					5
#define SA_MOVING_TO_REFERENCE_STATUS			6

// movement directions (for SA_MoveToEndStop_X and SA_SetSafeDirection_X)
#define SA_BACKWARD_DIRECTION					0
#define SA_FORWARD_DIRECTION					1

// auto zero (for SA_MoveToEndStop_X)
#define SA_NO_AUTO_ZERO							0
#define SA_AUTO_ZERO							1

// sensor presence (for SA_GetSensorPresent_X)
#define SA_NO_SENSOR_PRESENT					0
#define SA_SENSOR_PRESENT						1

// sensor types (for SA_SetSensorType_S)
#define SA_M_SENSOR_TYPE						1	// standard linear positioner
#define SA_GA_SENSOR_TYPE						2	// goniometer with 43.5mm radius
#define SA_GB_SENSOR_TYPE						3	// goniometer with 56.0mm raidus
#define SA_GC_SENSOR_TYPE						4	// rotary positioner with end stops, 85mm radius
#define SA_GD_SENSOR_TYPE						5	// goniometer with 60.5mm radius
#define SA_GE_SENSOR_TYPE						6	// goniometer with 77.5mm raidus
#define SA_RA_SENSOR_TYPE						7	// rotary with absolute position
#define SA_GF_SENSOR_TYPE						8	// rotary positioner with end stops, type SR1209m
#define SA_RB_SENSOR_TYPE						9	// rotary positioner, type SR1910m
#define SA_SR36M_SENSOR_TYPE					10	// rotary positioner, type SR3610m
#define SA_SR36ME_SENSOR_TYPE					11	// rotary positioner, type SR3610m, end stops
#define SA_SR50M_SENSOR_TYPE					12	// rotary positioner, type SR5018m
#define SA_SR50ME_SENSOR_TYPE					13	// rotary positioner, type SR5018m, end stops

// positioner alignments (for SA_SetPositionerAlignment_X)
#define SA_HORIZONTAL_ALIGNMENT					0
#define SA_VERTICAL_ALIGNMENT					1

// compatibility definitions
#define SA_NO_SENSOR_TYPE						0
#define SA_L180_SENSOR_TYPE						1
#define SA_G180R435_SENSOR_TYPE					2
#define SA_G180R560_SENSOR_TYPE					3
#define SA_G50R85_SENSOR_TYPE					4


#ifdef __cplusplus
extern "C" {
#endif

/************************************************************************
*************************************************************************
**                 Section I: Initialization Functions                 **
*************************************************************************
************************************************************************/

SCU3DCONTROL_API
SA_STATUS SA_GetDLLVersion(unsigned int *version);

SCU3DCONTROL_API
SA_STATUS SA_GetAvailableDevices(unsigned int *idList, unsigned int *idListSize);

SCU3DCONTROL_API
SA_STATUS SA_AddDeviceToInitDevicesList(unsigned int deviceId);

SCU3DCONTROL_API
SA_STATUS SA_ClearInitDevicesList();

SCU3DCONTROL_API
SA_STATUS SA_InitDevices(unsigned int configuration);

SCU3DCONTROL_API
SA_STATUS SA_ReleaseDevices();

SCU3DCONTROL_API
SA_STATUS SA_GetNumberOfDevices(unsigned int *number);

SCU3DCONTROL_API
SA_STATUS SA_GetDeviceID(SA_INDEX deviceIndex, unsigned int *deviceId);

SCU3DCONTROL_API
SA_STATUS SA_GetDeviceFirmwareVersion(SA_INDEX deviceIndex, unsigned int *version);


/************************************************************************
*************************************************************************
**        Section IIa:  Functions for SYNCHRONOUS communication        **
*************************************************************************
************************************************************************/

/*************************************************
**************************************************
**    Section IIa.1: Configuration Functions    **
**************************************************
*************************************************/
SCU3DCONTROL_API
SA_STATUS SA_SetClosedLoopMaxFrequency_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int frequency);

SCU3DCONTROL_API
SA_STATUS SA_GetClosedLoopMaxFrequency_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int *frequency);

SCU3DCONTROL_API
SA_STATUS SA_SetZero_S(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_GetSensorPresent_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int *present);

SCU3DCONTROL_API
SA_STATUS SA_SetSensorType_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int type);

SCU3DCONTROL_API
SA_STATUS SA_GetSensorType_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int *type);

SCU3DCONTROL_API
SA_STATUS SA_SetPositionerAlignment_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int alignment, unsigned int forwardAmplitude, unsigned int backwardAmplitude);

SCU3DCONTROL_API
SA_STATUS SA_GetPositionerAlignment_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int *alignment, unsigned int *forwardAmplitude, unsigned int *backwardAmplitude);

SCU3DCONTROL_API
SA_STATUS SA_SetSafeDirection_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int direction);

SCU3DCONTROL_API
SA_STATUS SA_GetSafeDirection_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int *direction);

/*************************************************
**************************************************
**  Section IIa.2: Movement Control Functions   **
**************************************************
*************************************************/
SCU3DCONTROL_API
SA_STATUS SA_MoveStep_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int steps, unsigned int amplitude, unsigned int frequency);

SCU3DCONTROL_API
SA_STATUS SA_SetAmplitude_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int amplitude);

SCU3DCONTROL_API
SA_STATUS SA_MovePositionAbsolute_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int position, unsigned int holdTime);

SCU3DCONTROL_API
SA_STATUS SA_MovePositionRelative_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int diff, unsigned int holdTime);

SCU3DCONTROL_API
SA_STATUS SA_MoveAngleAbsolute_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int angle, signed int revolution, unsigned int holdTime);

SCU3DCONTROL_API
SA_STATUS SA_MoveAngleRelative_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int angleDiff, signed int revolutionDiff, unsigned int holdTime);

SCU3DCONTROL_API
SA_STATUS SA_CalibrateSensor_S(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_MoveToReference_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int holdTime, unsigned int autoZero);

SCU3DCONTROL_API
SA_STATUS SA_MoveToEndStop_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int direction, unsigned int holdTime, unsigned int autoZero);

SCU3DCONTROL_API
SA_STATUS SA_Stop_S(SA_INDEX deviceIndex, SA_INDEX channelIndex);

/************************************************
*************************************************
**  Section IIa.3: Channel Feedback Functions  **
*************************************************
*************************************************/
SCU3DCONTROL_API
SA_STATUS SA_GetStatus_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int *status);

SCU3DCONTROL_API
SA_STATUS SA_GetAmplitude_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int *amplitude);

SCU3DCONTROL_API
SA_STATUS SA_GetPosition_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int *position);

SCU3DCONTROL_API
SA_STATUS SA_GetAngle_S(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int *angle, signed int *revolution);

/************************************************************************
*************************************************************************
**       Section IIb:  Functions for ASYNCHRONOUS communication        **
*************************************************************************
************************************************************************/

/*************************************************
**************************************************
**    Section IIb.1: Configuration Functions    **
**************************************************
*************************************************/
SCU3DCONTROL_API
SA_STATUS SA_SetClosedLoopMaxFrequency_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int frequency);

SCU3DCONTROL_API
SA_STATUS SA_GetClosedLoopMaxFrequency_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_SetZero_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_GetSensorPresent_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_SetSensorType_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int type);

SCU3DCONTROL_API
SA_STATUS SA_GetSensorType_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_SetPositionerAlignment_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int alignment, unsigned int forwardAmplitude, unsigned int backwardAmplitude);

SCU3DCONTROL_API
SA_STATUS SA_GetPositionerAlignment_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_SetSafeDirection_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int direction);

SCU3DCONTROL_API
SA_STATUS SA_GetSafeDirection_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_SetReportOnComplete_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int report);

/*************************************************
**************************************************
**  Section IIb.2: Movement Control Functions   **
**************************************************
*************************************************/
SCU3DCONTROL_API
SA_STATUS SA_MoveStep_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int steps, unsigned int amplitude, unsigned int frequency);

SCU3DCONTROL_API
SA_STATUS SA_SetAmplitude_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int amplitude);

SCU3DCONTROL_API
SA_STATUS SA_MovePositionAbsolute_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int position, unsigned int holdTime);

SCU3DCONTROL_API
SA_STATUS SA_MovePositionRelative_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int diff, unsigned int holdTime);

SCU3DCONTROL_API
SA_STATUS SA_MoveAngleAbsolute_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int angle, signed int revolution, unsigned int holdTime);

SCU3DCONTROL_API
SA_STATUS SA_MoveAngleRelative_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, signed int angleDiff, signed int revolutionDiff, unsigned int holdTime);

SCU3DCONTROL_API
SA_STATUS SA_CalibrateSensor_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_MoveToReference_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int holdTime, unsigned int autoZero);

SCU3DCONTROL_API
SA_STATUS SA_MoveToEndStop_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int direction, unsigned int holdTime, unsigned int autoZero);

SCU3DCONTROL_API
SA_STATUS SA_Stop_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

/************************************************
*************************************************
**  Section IIb.3: Channel Feedback Functions  **
*************************************************
************************************************/
SCU3DCONTROL_API
SA_STATUS SA_GetStatus_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_GetAmplitude_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_GetPosition_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

SCU3DCONTROL_API
SA_STATUS SA_GetAngle_A(SA_INDEX deviceIndex, SA_INDEX channelIndex);

/******************
* Answer retrieval
******************/
SCU3DCONTROL_API
SA_STATUS SA_SetReceiveNotification_A(SA_INDEX deviceIndex, HANDLE event);

SCU3DCONTROL_API
SA_STATUS SA_ReceiveNextPacket_A(SA_INDEX deviceIndex, unsigned int timeout, SA_PACKET *packet);

SCU3DCONTROL_API
SA_STATUS SA_ReceiveNextPacketIfChannel_A(SA_INDEX deviceIndex, SA_INDEX channelIndex, unsigned int timeout, SA_PACKET *packet);

SCU3DCONTROL_API
SA_STATUS SA_LookAtNextPacket_A(SA_INDEX deviceIndex, unsigned int timeout, SA_PACKET *packet);

SCU3DCONTROL_API
SA_STATUS SA_DiscardPacket_A(SA_INDEX deviceIndex);


#ifdef __cplusplus
}
#endif

#endif /* HCU3DCONTROL_H */
