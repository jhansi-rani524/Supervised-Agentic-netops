from netmiko import ConnectHandler
router = {
    "device_type" : "cisco_ios",
    "host" : "192.168.160.132",
    "username": "jhansi",
    "password": "mathematics322@",
    "secret" : ":mathematics322@"
}
#BGP states considered "down"
down_states = ["Idle", "Active", "Connect"]

try:
    #Connect to the router
    connection = ConnectHandler (**router)
    connection.enable()

    #Run BGP neighbor command
    bgp_output =  connection.send_command("sh ip bgp summary")
    print ("\n: Full BGP Summary Output:\n")
    print(bgp_output)

    print("\n BGP neighbors which are Down:\n")

    #skip the lines untill we find the header
    lines = bgp_output.strip().splitlines()
    for index, line in enumerate(lines):
        if line.strip().startswith("Neighbor"):
            data_lines = lines [index + 1: ] #get all the lines after the header
            break
    else:
            print ("No BGP Summary data found:")
            data_lines = []
    for line in data_lines:
        if not line.strip():
            continue
        
        fields = line.split()
        if len(fields)  < 9:
            continue  #not a valid BGP neighbor
        neighbor_ip =  fields[0]
        last_field = fields[-1]
        second_field = fields [-2]

        #check if state is string
        if last_field in down_states:
            print (f" Neighbor {neighbor_ip} is in state {last_field}")
        elif not last_field.isdigit() and second_field():
             print (f" Neighbor {neighbor_ip} is in state {last_field}")

except Exception as e:
    print(f" error {e}:")                


finally:
    try:
        connection.disconnect()
    except:
        pass    



