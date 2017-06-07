import xml.etree.cElementTree as ET
import data

food_amenities = ["restaurant", "cafe", "pub", "bar", "fast_food", "delicatessen"]

def is_food_node(tag):
    cuisine_tag = tag.attrib['k'] == "cuisine"
    food_amenity_tag = (tag.attrib['k'] == "amenity" and tag.attrib['v'] in food_amenities)
    return cuisine_tag or food_amenity_tag

def audit(osmfile):
    osm_file = open(osmfile, "r")
    food_nodes = []
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_food_node(tag):
                    food_nodes.append(data.shape_element(elem))
                    break
    osm_file.close()
    return food_nodes
