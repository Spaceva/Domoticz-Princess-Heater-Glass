"""
<plugin key="PrincessSmartGlassPanelHeater" name="Princess Smart Glass Panel Heater" author="gweber" version="1.0.0" wikilink="https://github.com/Spaceva/Domoticz-Princess-Heater-Glass">
    <description>
        <h2>Princess Smart Glass Panel Heater Plugin</h2><br/>
        <p><strong>All controls are managed using  <a href="https://github.com/jasonacox/tinytuya">TinyTuya</a>, so make sure it is installed.</strong></p>
        <p>You will need information from TinyTuya for the plugin to work.</p>        
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Displays the temperature of the room where the heater is located.</li>
            <li>Controls the heater: switch on/off, adjust temperature, set a timer, enable/disable child lock, and toggle between low/high mode.</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>Main switch - Controls the heater mode: off, low, and high.</li>
            <li>Set Temperature - Adjusts the desired room temperature.</li>
            <li>Current Temperature - Displays the current room temperature.</li>
            <li>Timer - Controls the timer.</li>
            <li>Child Lock - Toggles the child lock on/off.</li>
        </ul>
    </description>
    <params>
        <param field="Mode1" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Mode2" label="Local Device Tuya ID" width="250px" required="true" default=""/>
        <param field="Mode3" label="Local Device Tuya Key" width="250px" required="true" default=""/>
        <param field="Mode4" label="Tuya Version" width="30px" required="true" default="3.4"/>
        <param field="Mode5" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true"/>
            </options>
        </param>
    </params>
</plugin>
"""
try:
    import DomoticzEx as Domoticz
except ImportError:
    import fakeDomoticz as Domoticz
import tinytuya

class BasePlugin:
    enabled = False
    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode5"] == "Debug":
            Domoticz.Debugging(1)
            Domoticz.Debug("Debug mode enabled")
        
        Domoticz.Debug("onStart called")
        self.tuyaDevice = TuyaDevice()
        CreateDevicesIfNecessary()

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onCommand(self, DeviceID, Unit, Command, Level, Color):
        Domoticz.Debug("onCommand called for Device " + str(DeviceID) + " Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        tuyaDeviceState = self.tuyaDevice.status()
        isMainSwitchOn=tuyaDeviceState['dps']['1']
        device=Devices[DeviceID].Units[Unit]
            
        if Unit == 2:
            if Command == 'Off':
                self.tuyaDevice.set_value(1, False)
                self.tuyaDevice.set_value(7, 'Low')
                device.nValue=0
                device.sValue="0"
            
            elif Command == 'Set Level':
                self.tuyaDevice.set_value(1, True)
                self.tuyaDevice.set_value(7, 'High' if Level == 20 else 'Low')
                device.nValue=1
                device.sValue=str(Level)
            
            device.Update(Log=True)
        
        elif isMainSwitchOn is False:
            Domoticz.Log("Main Switch is off so device can't be changed.")
            return
            
        elif Unit == 3:
            if Command == 'Off':
                self.tuyaDevice.set_value(2, False)
                device.nValue=0
                device.sValue="Off"
            
            elif Command == 'On':
                self.tuyaDevice.set_value(2, True)
                device.nValue=1
                device.sValue="On"
            
            device.Update(Log=True)
        
        elif Unit == 4:
            if float(Level) < 15.0 or float(Level) > 35.0:
                Domoticz.Log("Temperature range is between 15 and 35°C.")
                return

            self.tuyaDevice.set_value(3, float(Level))
            device.sValue=str(Level)
            device.Update(Log=True)
        
        elif Unit == 5:
            if float(Level) < 0 or float(Level) > 1440:
                Domoticz.Log("Timer range is between 0 and 1440 min (24h).")
                return

            self.tuyaDevice.set_value(5, float(Level))
            device.sValue=str(Level)
            device.Update(Log=True)
         
    def onHeartbeat(self):
        if not hasattr(self, 'tuyaDevice') or self.tuyaDevice is None:
            self.tuyaDevice = TuyaDevice()
            
        tuyaDeviceState = self.tuyaDevice.status()
        UpdateDevices(tuyaDeviceState)
        DumpStateToDebug(tuyaDeviceState)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()
    
def onStop():
    global _plugin
    _plugin.onStop()

def onCommand(DeviceID, Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(DeviceID, Unit, Command, Level, Color)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
    
def DumpStateToDebug(data):
    Domoticz.Debug("Main Switch: "+ str(data['dps']['1']))
    Domoticz.Debug("Child Lock: "+ str(data['dps']['2']))
    Domoticz.Debug("Set Temperature: "+ str(data['dps']['3'])+'°C')
    Domoticz.Debug("Current Temperature: "+ str(data['dps']['4'])+'°C')
    Domoticz.Debug("Timer: "+ str(data['dps']['5'])+'min')
    Domoticz.Debug("Mode: "+ str(data['dps']['7']))

def DumpConfigToLog():
    Domoticz.Debug("Devices count: " + str(len(Devices)))
    for DeviceName in Devices:
        Device = Devices[DeviceName]
        Domoticz.Debug("Device ID:       '" + str(Device.DeviceID) + "'")
        Domoticz.Debug("---> Units Count:      '" + str(len(Device.Units)) + "'")
        for UnitNo in Device.Units:
            Unit = Device.Units[UnitNo]
            Domoticz.Debug("---> Unit:           " + str(UnitNo))
            Domoticz.Debug("---> Unit Name:     '" + Unit.Name + "'")
            Domoticz.Debug("---> Unit nValue:    " + str(Unit.nValue))
            Domoticz.Debug("---> Unit sValue:   '" + Unit.sValue + "'")
            Domoticz.Debug("---> Unit LastLevel: " + str(Unit.LastLevel))
    return

def TuyaDevice():
    return tinytuya.Device(dev_id=Parameters["Mode2"], address=Parameters["Mode1"], local_key=Parameters["Mode3"], version= Parameters["Mode4"])

def CreateDevicesIfNecessary():
    Domoticz.Log("Creating Devices...")
    if "Temp" not in Devices:
        Domoticz.Unit(Name="Current Temperature", DeviceID="Temp", Unit=1, Type=80,Description="Displays the heater's room current temperature.", Used=1).Create()
        Domoticz.Log("Created device: " + Devices["Temp"].Units[1].Name + ".")
        
    if "MainSwitch" not in Devices:
        options = {
            "LevelNames": "Off|Low|High",
            "LevelActions": "|||",
            "SelectorStyle": "0",
            "LevelOffHidden": "false"
        }
        Domoticz.Unit(Name="Main Switch", DeviceID="MainSwitch", Unit=2, TypeName="Selector Switch", Switchtype=18, Options=options, Description="Power on/off and mode.", Image=9, Used=1).Create()
        Domoticz.Log("Created device: " + Devices["MainSwitch"].Units[2].Name + ".")
        
    if "ChildLock" not in Devices:
        Domoticz.Unit(Name="Child Lock", DeviceID="ChildLock", Unit=3, TypeName="Switch", Switchtype=0, Description="Child lock on/off.", Image=9, Used=1).Create()
        Domoticz.Log("Created device: " + Devices["ChildLock"].Units[3].Name + ".")
        
    if "SetTemperature" not in Devices:
        options={'ValueStep':'1', 'ValueMin':'15', 'ValueMax':'35', 'ValueUnit':'°C'}
        Domoticz.Unit(Name="Set Temperature", DeviceID="SetTemperature", Unit=4, Type=242, Subtype=1, Options=options, Description="Desired Temperature.", Image=15, Used=1).Create()
        Domoticz.Log("Created device: " + Devices["SetTemperature"].Units[4].Name + ".")
        
    if "SetTemperature" not in Devices:
        options={'ValueStep':'1', 'ValueMin':'15', 'ValueMax':'35', 'ValueUnit':'°C'}
        Domoticz.Unit(Name="Set Temperature", DeviceID="SetTemperature", Unit=4, Type=242, Subtype=1, Options=options, Description="Desired Temperature.", Image=15, Used=1).Create()
        Domoticz.Log("Created device: " + Devices["SetTemperature"].Units[4].Name + ".")
        
    if "Timer" not in Devices:
        options={'ValueStep':'1', 'ValueMin':'0', 'ValueMax':'1440', 'ValueUnit':'min'}
        Domoticz.Unit(Name="Timer", DeviceID="Timer", Unit=5, Type=242, Subtype=1, Options=options, Description="Timer.", Image=21, Used=1).Create()
        Domoticz.Log("Created device: " + Devices["Timer"].Units[5].Name + ".")

def UpdateDevices(tuyaDeviceState):
    isMainSwitchOn=tuyaDeviceState['dps']['1']
    isChildLockOn=tuyaDeviceState['dps']['2']
    setTemperature=str(tuyaDeviceState['dps']['3'])
    currentTemperature=str(tuyaDeviceState['dps']['4'])
    timer=str(tuyaDeviceState['dps']['5'])
    mode=str(tuyaDeviceState['dps']['7'])
    level="20" if mode == "High" else "10"
    Devices["Temp"].Units[1].sValue=currentTemperature
    Devices["Temp"].Units[1].Update(Log=True)
    Devices["MainSwitch"].Units[2].sValue=level if isMainSwitchOn else "0"
    Devices["MainSwitch"].Units[2].nValue=1 if isMainSwitchOn else 0
    Devices["MainSwitch"].Units[2].Update(Log=True)
    Devices["ChildLock"].Units[3].sValue="On" if isChildLockOn else "Off"
    Devices["ChildLock"].Units[3].nValue=1 if isChildLockOn else 0
    Devices["ChildLock"].Units[3].Update(Log=True)
    Devices["SetTemperature"].Units[4].sValue=setTemperature
    Devices["SetTemperature"].Units[4].Update(Log=True)
    Devices["Timer"].Units[5].sValue=timer
    Devices["Timer"].Units[5].Update(Log=True)