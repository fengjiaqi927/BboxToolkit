import matplotlib
import random


classes = [
        # 'Ship': 
            'Passenger Ship', 'Motorboat', 'Fishing Boat', 'Tugboat', 'other-ship',
                   'Engineering Ship', 'Liquid Cargo Ship', 'Dry Cargo Ship', 'Warship',
        # 'Vehicle': 
            'Small Car', 'Bus', 'Cargo Truck', 'Dump Truck', 'other-vehicle',
                      'Van', 'Trailer', 'Tractor', 'Excavator', 'Truck Tractor',
        #'Airplane': 
            'Boeing737', 'Boeing747', 'Boeing777', 'Boeing787', 'ARJ21',
                       'C919', 'A220', 'A321', 'A330', 'A350', 'other-airplane',
        #'Court': 
            'Baseball Field', 'Basketball Court', 'Football Field', 'Tennis Court',
        #'Road': 
            'Roundabout', 'Intersection', 'Bridge']

hex_list = list()

for name, hex in matplotlib.colors.cnames.items():
    hex_list.append(hex)
    print(hex)

hex_for_class = random.sample(hex_list, len(classes))

fire_name = "./vis_configs/isprs/colors.txt"

f = open(fire_name,'w')

for hex, classname in zip(hex_for_class,classes):
    txt_line = hex + ' $' + classname
    f.write(txt_line + '\n')

f.close()

print('done')

