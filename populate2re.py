import os
from copy import deepcopy
import re

SOURCE_PATH = '../../_Collection_Decompiled/Transcendence'

xml_files = {}

for r, _, fs in os.walk(SOURCE_PATH):
    for f in fs:
        if not f.endswith('.xml'): continue
        with open(os.path.join(r,f),'rb') as _f:
            xml_files[f] = {'full_path': os.path.join(r,f), 'contents':_f.read()}

def get_types_by_inner_xml(contents, inner_xml_search, outer_xml_start, outer_xml_end, inner_xml_replace, outer_xml_start_replace, outer_xml_end_replace):
    contents_chunks = re.split(inner_xml_search, contents, flags=re.I)
    if len(contents_chunks) == 1:
        return [] #failed to find any
    results = []
    for i in range(len(contents_chunks)-1):
        chunk_start = contents_chunks[i]
        chunk_end = contents_chunks[i+1]
        type_start = outer_xml_start_replace + re.split(outer_xml_start, chunk_start, flags=re.I)[-1]
        type_end = re.split(outer_xml_end, chunk_end, flags=re.I)[0] + outer_xml_end_replace
        full_type = type_start + inner_xml_replace + type_end
        results.append(full_type)
    return results

ITEM_XML = [(b'<\s*ItemType',b'<ItemType'), (b'</\s*ItemType\s*>',b'</ItemType>')]    

def cat(lst, *args):
    lst = deepcopy(lst)
    for a in args:
        lst.append(a)
    return lst

SEARCH_TYPES = {
    #b'<Weapon': cat(ITEM_XML,'DGR_Weapons.xml'),
    #b'<Armor': cat(ITEM_XML,'DGR_Armors.xml'),
    #b'<Shield': cat(ITEM_XML,'DGR_Shields.xml'),
    #b'<AutoDefenseDevice': cat(ITEM_XML,'DGR_Autodefense.xml'),
    #b'<RepairerDevice': cat(ITEM_XML, 'DGR_Repairers.xml'),
    #b'<Device': cat(ITEM_XML, 'DGR_Devices.xml'),
    b'UNID\s*=\s*"&it': [
        (b'<\s*ItemType',b'<ItemType'),
        (b'</\s*ItemType\s*>',b'</ItemType>'),
        {
            b'<\s*Weapon':'DGR_Weapons.xml',
            b'<\s*Armor':'DGR_Armors.xml',
            b'<\s*Shield':'DGR_Shields.xml',
            b'<\s*AutoDefenseDevice':'DGR_AutoDefenses.xml',
            b'<\s*RepairerDevice':'DGR_Repairers.xml',
            b'<\s*DriveDevice':'DGR_Drives.xml',
            b'<\s*ReactorDevice':'DGR_Reactors.xml',
            b'<\s*CyberDeckDevice':'DGR_CyberDecks.xml',
            b'<\s*CargoHoldDevice':'DGR_CargoHolds.xml',
            b'<\s*SolarDevice':'DGR_SolarDevices.xml',
            b'<\s*MiscellaneousDevice':'DGR_Devices.xml',
            #b'<\s*Missile':'DGR_Ammo.xml',
            b'.*':'DGR_Items.xml'
        },
        b'UNID="&it'],
    b'UNID\s*=\s*"&sc': [
        (b'<\s*ShipClass',b'<ShipClass'),
        (b'</\s*ShipClass\s*>',b'</ShipClass>'),
        {b'<': 'DGR_ships.xml'},
        b'UNID="&sc'],
    b'UNID\s*=\s*"&st': [
        (b'<\s*StationType',b'<StationType'),
        (b'</\s*StationType\s*>',b'</StationType>'),
        {b'<': 'DGR_stations.xml'},
        b'UNID="&st'],
}

buckets = {}
assigned = set()

for t in SEARCH_TYPES:
    print(SEARCH_TYPES[t])
    s, e, o, t_ = SEARCH_TYPES[t] #start, end, output, type_Replacement
    s, s_ = s
    e, e_ = e
    for o_req in o:
        bucket = o[o_req]
        if not bucket in buckets:
            buckets[bucket] = {}
        for f in xml_files:
            if not f in buckets[bucket]:
                buckets[bucket][f] = []
            types = get_types_by_inner_xml(xml_files[f]['contents'], t, s, e, t_, s_, e_)
            for _t in types:
                if _t in assigned: continue
                if re.findall(o_req, _t, flags=re.I):
                    buckets[bucket][f].append(_t)
                    assigned.add(_t)
                    try:
                        print(_t.decode('utf-8'))
                    except:
                        try:
                            print(_t.decode('ascii'))
                        except:
                            print(_t)


#workaround for ammo being inconsistently handled:
ammo_bucket = buckets['DGR_Ammo.xml'] = {}
weapon_bucket = buckets['DGR_Weapons.xml']
item_bucket = buckets['DGR_Items.xml']
ammo_unids = []
for sf_w in weapon_bucket:
    for itm in weapon_bucket[sf_w]:
        chunks = re.split(b'ammoId\s*=\s*"&', itm, flags=re.I)[1:]
        for chunk in chunks:
            ammo_unids.append(chunk.split(b';"')[0])
for sf_i in item_bucket:
    bucket_replace = []
    ammo_sf = ammo_bucket[sf_i] = []
    for itm in item_bucket[sf_i]:
        found = False
        for ammo_unid in ammo_unids:
            if re.findall(b'UNID\s*=\s*"&%s' % ammo_unid, itm, flags=re.I):
                ammo_sf.append(itm)
                found = True
                break
        if found: continue
        bucket_replace.append(itm)
    item_bucket[sf_i] = bucket_replace



HEADER = b'''<?xml version="1.0" encoding="utf-8"?>

<TranscendenceModule>
'''


FOOTER = b'''</TranscendenceModule>'''

for bucket in buckets:
    print('doing bucket %s' % bucket)
    with open('./_auto_xml/%s' % bucket, 'wb') as f:
        f.write(HEADER)
        for sf in buckets[bucket]:
            print('doing source file %s' % sf)
            f.write(b'<!-- %s -->\n' % bytes(sf, encoding='utf-8'))
            for entry in buckets[bucket][sf]:
                f.write(entry)
                f.write(b'\n')
        f.write(FOOTER)
