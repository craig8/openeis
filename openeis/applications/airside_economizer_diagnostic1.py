'''
Copyright (c) 2014, Battelle Memorial Institute
All rights reserved.
   
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met: 
   
1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer. 
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution. 
   
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
   
The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies, 
either expressed or implied, of the FreeBSD Project.
'''
'''
This material was prepared as an account of work sponsored by an 
agency of the United States Government.  Neither the United States 
Government nor the United States Department of Energy, nor Battelle,
nor any of their employees, nor any jurisdiction or organization 
that has cooperated in the development of these materials, makes 
any warranty, express or implied, or assumes any legal liability 
or responsibility for the accuracy, completeness, or usefulness or 
any information, apparatus, product, software, or process disclosed,
or represents that its use would not infringe privately owned rights.
   
Reference herein to any specific commercial product, process, or 
service by trade name, trademark, manufacturer, or otherwise does 
not necessarily constitute or imply its endorsement, recommendation, 
r favoring by the United States Government or any agency thereof, 
or Battelle Memorial Institute. The views and opinions of authors 
expressed herein do not necessarily state or reflect those of the 
United States Government or any agency thereof.
   
PACIFIC NORTHWEST NATIONAL LABORATORY
operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
under Contract DE-AC05-76RL01830
'''
import datetime
from collections import Counter
from openeis.applications.airside_sensor_driven_app import Application as app
from openeis.applications import (DrivenApplicationBaseClass,
                                  OutputDescriptor, 
                                  ConfigDescriptor,
                                  InputDescriptor,
                                  Results)
import logging
   
class Application(DrivenApplicationBaseClass):
    """
    Air-side HVAC diagnostic to check if an AHU/RTU is not economizing when it should.
    """
    '''Diagnostic Point Names (Must match Openeis data-type names)'''
    fan_status_name = "fan_status"
    oa_temp_name = "oa_temp"
    ma_temp_name = "ma_temp"
    ra_temp_name = "ra_temp"
    damper_signal_name = "damper_signal"
    cool_call_name = "cool_call"
    
    def __init__(self,*args,device_type=None,economizer_type=None,temp_deadband=1.0,
                data_window=None, mat_low_threshold=None,mat_high_threshold=None,oat_low_threshold=None,
                oat_high_threshold=None,rat_low_threshold=None,rat_high_threshold=None,open_damper_threshold=None,
                oaf_economizing_threshold=None,oaf_temperature_threshold=None,cooling_enabled_threshold=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.damper_signal_values = []
        self.cool_call_values = []
        self.economizer_control = []
        self.timestamp = []
        self.pre_requiste_messages = []
        self.pre_msg_time = []
        self.economizer_diagnostic1_result = []
   
        '''Pre-requisite messages'''
        self.pre_msg0 ='Air temperature sensor problem detected, economizer diagnostics depend on reliable air temperature sensor readings.'
        self.pre_msg1 ='Supply fan is off, current data will not be used for diagnostics.'
        self.pre_msg2 ='Outside-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        self.pre_msg3 ='Return-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        self.pre_msg4 ='Mixed-air temperature is outside high/low operating limits, check the functionality of the temperature sensor.'
        self.pre_msg5 ='Must verify temperature sensors functionality before running economizer diagnostics.'
        self.pre_msg6 ='Unit is not cooling, this diagnostic is only performed when the system is actively cooling.'
        self.pre_msg7 ='Conditions consistently not favorable for economizing - Try diagnostic later'
        self.pre_msg8 ='Conditions are not favorable for a reliable OAF calculation, the outdoor-air temperature and the' \
                        ' return-air temperature are too close.'
 
        '''Algorithm result messages'''
        self.alg_result_messages =['Conditions are favorable for economizing but the damper is frequently below 100% open',
                                  'No problems were detected for this economizer diagnostic',
                                  'Conditions are favorable for economizing and the damper is 100% open but the OAF indicates the unit is not brining in near 100% OA']

        '''Point names (Configurable)'''
        self.fan_status_name = Application.fan_status_name
        self.oa_temp_name =  Application.oa_temp_name
        self.ra_temp_name =  Application.ra_temp_name
        self.ma_temp_name =  Application.ma_temp_name
        self.damper_signal_name = Application.damper_signal_name
        self.cool_call_name = Application.cool_call_name  #Cooling coil valve position for AHU and cooling call (compressor command) for RTU
        
        self.device_type = device_type.lower()
        temp = [x.strip() for x in economizer_type.split(',')]
        self.economizer_type = [float(element) if (len(temp) == 2 and (element != 'DDB' and element != 'HL')) else element for element in temp]   #0 for differential dry bulb and 1 for high limit
        self.economizer_type = [element.lower() if isinstance(element,str) else element for element in self.economizer_type]

        '''Application thresholds (Configurable)'''
        self.data_window = float(data_window)
        self.mat_low_threshold = float(mat_low_threshold)
        self.mat_high_threshold = float(mat_high_threshold)
        self.oat_low_threshold = float(oat_low_threshold)
        self.oat_high_threshold = float(oat_high_threshold)
        self.rat_low_threshold = float(rat_low_threshold)
        self.rat_high_threshold = float(rat_high_threshold)
        
        self.open_damper_threshold = float(open_damper_threshold)
        self.oaf_economizing_threshold = float(oaf_economizing_threshold)
        self.temp_deadband = float(temp_deadband)
        self.oaf_temperature_threshold = float(oaf_temperature_threshold)
        self.cooling_enabled_threshold = float(cooling_enabled_threshold)

    @classmethod
    def get_config_parameters(cls):
        '''
        Generate required configuration
        parameters with description for user
        '''
        return {
            'device_type': ConfigDescriptor(str, 'RTU or AHU'),
            'economizer_type': ConfigDescriptor(str, 'DDB or HL, value'),
            'data_window': ConfigDescriptor(float, 'Data Window'),
            'mat_low_threshold': ConfigDescriptor(float, 'Mixed-air sensor low limit'),
            'mat_high_threshold': ConfigDescriptor(float, 'Mixed-air sensor high limit'),
            'rat_low_threshold': ConfigDescriptor(float, 'Return-air sensor low limit'),
            'rat_high_threshold': ConfigDescriptor(float, 'Return-air sensor high limit'),
            'oat_low_threshold': ConfigDescriptor(float, 'Outdoor-air sensor low limit'),
            'oat_high_threshold': ConfigDescriptor(float, 'Outdoor-air sensor high limit'),
            
            'temp_deadband': ConfigDescriptor(float,'Economizer control temperature deadband'),
            'oat_mat_difference_threshold': ConfigDescriptor(float,'Consistency check for OAT and MAT when outdoor-air damper is 100% open'),
            'open_damper_threshold': ConfigDescriptor(float, 'Threshold below 100% in which damper is considered fully open'),
            'oaf_economizing_threshold': ConfigDescriptor(float,'Amount below 1.0 in which the OAF is considered sufficient to economizer.'),
            'oaf_temperature_threshold': ConfigDescriptor(float,'Required difference between OAT and RAT for accurate diagnostic'),
            'cooling_enabled_threshold': ConfigDescriptor(float, 'Amount cooling coil valve must be open for diagnostic to consider unit in cooling mode')
           }

    @classmethod
    def required_input(cls):
        '''
        Generate required inputs with description for
        user.
        '''
        return {
            cls.fan_status_name: InputDescriptor('SupplyFanStatus', 'AHU Supply Fan Status', count_min=1),
            cls.oa_temp_name: InputDescriptor('OutdoorAirTemperature','AHU or building outdoor-air temperature', count_min=1),
            cls.ma_temp_name: InputDescriptor('MixedAirTemperature','AHU mixed-air temperature', count_min=1),
            cls.ra_temp_name: InputDescriptor('ReturnAirTemperature','AHU return-air temperature',count_min=1),
            cls.damper_signal_name: InputDescriptor('OutdoorDamperSignal','AHU outdoor-air damper signal', count_min=1),
            cls.cool_call_name: InputDescriptor('Cooling Call', 'AHU cooling coil command or RTU coolcall or compressor command', count_min=1)
            }

    def reports(self):
        '''
        Called by UI to create Viz.
        Describe how to present output to user
        Display this viz with these columns from this table
    
        display_elements is a list of display objects specifying viz and columns
        for that viz
        '''
        return []

    @classmethod
    def output_format(cls, input_object):
        """
        Called when application is staged.
        Output will have the date-time and  error-message.
        """
        result = super().output_format(input_object)
        
        topics = input_object.get_topics()
        diagnostic_topic = topics[cls.fan_status_name][0]
        diagnostic_topic_parts = diagnostic_topic.split('/')
        output_topic_base = diagnostic_topic_parts[:-1]
        datetime_topic = '/'.join(output_topic_base+['airside_low_dat_diagnostic', 'date'])
        message_topic = '/'.join(output_topic_base+['airside_low_dat_diagnostic', 'message'])
        output_needs = {
            'Diagnostic_Message': {
                'date-time': OutputDescriptor('datetime', datetime_topic),
                'diagnostic-message': OutputDescriptor('string', message_topic)
                }
            }
        result.update(output_needs)
        return result

    def drop_partial_lines (self): 
        '''
        drop rows with missing data.
        '''
        return True

     
    def run(self,current_time, points): 
        """
        Check algorithm pre-quisites and assemble analysis data set.
        """
        device_dict = {}
        diagnostic_result = Results()

        if None in points.values():
            diagnostic_result.log(''.join(['Missing data for timestamp: ',str(current_time),
                                   '  This row will be dropped from analysis.']))
            return diagnostic_result

        for key, value in points.items():
            device_dict[key.lower()] = value
   
        self.pre_msg_time.append(current_time)
        message_check =  datetime.timedelta(minutes=(self.data_window))

        if (self.pre_msg_time[-1]-self.pre_msg_time[0]) >= message_check:
            msg_lst = [self.pre_msg0, self.pre_msg1, self.pre_msg2, self.pre_msg3, self.pre_msg4, self.pre_msg5,
                       self.pre_msg6, self.pre_msg7, self.pre_msg8]
            for item in msg_lst:
                if self.pre_requiste_messages.count(item) > (0.25)*len(self.pre_msg_time):
                    diagnostic_result.log(item,logging.INFO)
            self.pre_requiste_messages = []
            self.pre_msg_time = []

        for key, value in device_dict.items():
            if key.startswith(self.fan_status_name): 
                if int(value) == 0:
                    self.pre_requiste_messages.append(self.pre_msg1)
                    return diagnostic_result

        try:
            if app.temp_sensor_problem == None:
                self.pre_requiste_messages.append(self.pre_msg5)
                return diagnostic_result
            elif self.pre_msg5 in self.pre_requiste_messages:
                self.pre_requiste_messages = [x for x in self.pre_requiste_messages if x != self.pre_msg5]
            if app.temp_sensor_problem == True:
                self.pre_requiste_messages.append(self.pre_msg0)
                return diagnostic_result
        except:
            pass
            
        damper_data, oatemp_data, matemp_data = [], [], []
        ratemp_data, cooling_data = [], [] 

        for key, value in device_dict.items():
            if key.startswith(self.damper_signal_name): 
                damper_data.append(value)

            elif key.startswith(self.oa_temp_name):
                oatemp_data.append(value)
                
            elif key.startswith(self.ma_temp_name):
                matemp_data.append(value)

            elif key.startswith(self.ra_temp_name):
                ratemp_data.append(value)
            
            elif key.startswith(self.cool_call_name):
                cooling_data.append(value)
        
        oatemp = (sum(oatemp_data)/len(oatemp_data))
        ratemp = (sum(ratemp_data)/len(ratemp_data))
        matemp = (sum(matemp_data)/len(matemp_data))
        damper_signal = (sum(damper_data)/len(damper_data))
        
        limit_check = False
        if oatemp < self.oat_low_threshold or oatemp > self.oat_high_threshold:
            self.pre_requiste_messages.append(self.pre_msg2)
            limit_check = True
        if ratemp < self.rat_low_threshold or ratemp > self.rat_high_threshold:
            self.pre_requiste_messages.append(self.pre_msg3)
            limit_check = True
        if matemp < self.mat_low_threshold or matemp > self.mat_high_threshold:
            self.pre_requiste_messages.append(self.pre_msg4)
            limit_check = True

        if limit_check:
            return diagnostic_result

        device_type_error = False
        if self.device_type == 'ahu':
            cooling_valve = sum(cooling_data)/len(cooling_data)
            if cooling_valve > self.cooling_enabled_threshold: 
                cooling_call = True
            else:
                cooling_call = False
        elif self.device_type == 'rtu':
            cooling_call = int(max(cooling_data))
        else:
            device_type_error = True
            diagnostic_result.log('device_type must be specified as "AHU" or "RTU"', logging.INFO)
            
        if device_type_error:
            return diagnostic_result
        
        if not cooling_call:
            self.pre_requiste_messages.append(self.pre_msg6)
            return diagnostic_result

        if self.economizer_type[0] == 'ddb':
            economizer_conditon = (oatemp < (ratemp - self.temp_deadband))
        else:
            economizer_conditon = (oatemp < (self.economizer_type[1] - self.temp_deadband))
 
        if not economizer_conditon:
            self.pre_requiste_messages.append(self.pre_msg7)
            return diagnostic_result

        if abs(oatemp - ratemp) >= self.oaf_temperature_threshold:
            self.oa_temp_values.append(oatemp), self.ma_temp_values.append(matemp), 
            self.ra_temp_values.append(ratemp), self.timestamp.append(current_time),
            self.damper_signal_values.append(damper_signal_data)
        else:
            self.pre_requiste_messages.append(self.pre_msg8)
            return diagnostic_result

        time_check =  datetime.timedelta(minutes=(self.data_window))
   
        if ((self.timestamp[-1]-self.timestamp[0]) >= time_check and
            len(self.timestamp) >= 30):
            diagnostic_result = self.not_economizing_when_needed(diagnostic_result)
        return diagnostic_result
       
    def not_economizing_when_needed(self, result):
        """
        If the detected problems(s) are consistent then generate a fault message(s).
        """
        oaf = [(m-r)/(o-r) for o,r,m in zip(self.oa_temp_values,self.ra_temp_values,self.ma_temp_values)]
        avg_oaf = sum(oaf)/len(oaf)*100.0
        avg_damper_signal = sum(self.damper_signal_values)/len(self.damper_signal_values)
        
        alg_message_count = Counter(self.economizer_control)
        alg_message_count = dict(alg_message_count)
   
        if  avg_damper_signal < self.open_damper_threshold:
            diagnostic_message = (self.alg_result_messages[1])
        else:
            if (100.0 - avg_oaf) <= self.oaf_economizing_threshold:
                diagnostic_message = (self.alg_result_messages[2])
            else:
                diagnostic_message = (self.alg_result_messages[3])

        result.log(item, logging.INFO)

        self.pre_msg_time = []
        self.pre_requiste_messages = []
        self.timestamp = []
        self.oa_temp_values = []
        self.ra_temp_values = []
        self.ma_temp_values = []
        self.economizer_control = []
        diagnostic_message = []
        return result