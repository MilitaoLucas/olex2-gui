#fragHAR script from Justin Bergmann, adapted by Florian Kleemiss for NoSpherA2 comaptibility
#fragHAR assumes ORCA 5.0 as the wfn software!

import numpy as np
import copy
import os
from olexFunctions import OV

cov_rad=[
    #THESE ARE THE VALUES FROM THE ORIGINAL SCRIPT
    #["H",0.31],["D",0.31],
    #["C",0.76],["N",0.71],
    #["O",0.66],["S",1.05],
    #["Fe",1.52],["dum",0.0]
    #THESE ARE THE CSD VALUES OF VOVALENT RADII
    ["H" ,0.23],
    ["He",1.5 ],
    ["Li",1.28],
    ["Be",0.96],
    ["B" ,0.83],
    ["C" ,0.68],
    ["N" ,0.68],
    ["O" ,0.68],
    ["F" ,0.64],
    ["Ne",1.5 ],
    ["Na",1.66],
    ["Mg",1.41],
    ["Al",1.21],
    ["Si",1.2 ],
    ["P" ,1.05],
    ["S" ,1.02],
    ["Cl",0.99],
    ["Ar",1.51],
    ["K" ,2.03],
    ["Ca",1.76],
    ["Sc",1.7 ],
    ["Ti",1.6 ],
    ["V" ,1.53],
    ["Cr",1.39],
    ["Mn",1.61],
    ["Fe",1.52],
    ["Co",1.26],
    ["Ni",1.24],
    ["Cu",1.32],
    ["Zn",1.22],
    ["Ga",1.22],
    ["Ge",1.17],
    ["As",1.21],
    ["Se",1.22],
    ["Br",1.21],
    ["Kr",1.5 ],
    ["Rb",2.2 ],
    ["Sr",1.95],
    ["Y" ,1.9 ],
    ["Zr",1.75],
    ["Nb",1.64],
    ["Mo",1.54],
    ["Tc",1.47],
    ["Ru",1.46],
    ["Rh",1.42],
    ["Pd",1.39],
    ["Ag",1.45],
    ["Cd",1.54],
    ["In",1.42],
    ["Sn",1.39],
    ["Sb",1.39],
    ["Te",1.47],
    ["I" ,1.4 ],
    ["Xe",1.5 ],
    ["Cs",2.44],
    ["Ba",2.15],
    ["La",2.07],
    ["Ce",2.04],
    ["Pr",2.03],
    ["Nd",2.01],
    ["Pm",1.99],
    ["Sm",1.98],
    ["Eu",1.98],
    ["Gd",1.96],
    ["Tb",1.94],
    ["Dy",1.92],
    ["Ho",1.92],
    ["Er",1.89],
    ["Tm",1.9 ],
    ["Yb",1.87],
    ["Lu",1.87],
    ["Hf",1.75],
    ["Ta",1.7 ],
    ["W" ,1.62],
    ["Re",1.51],
    ["Os",1.44],
    ["Ir",1.41],
    ["Pt",1.36],
    ["Au",1.36],
    ["Hg",1.32],
    ["Tl",1.45],
    ["Pb",1.46],
    ["Bi",1.48],
    ["Po",1.4 ],
    ["At",1.21],
    ["Rn",1.5 ],
    ["Fr",2.6 ],
    ["Ra",2.21],
    ["Ac",2.15],
    ["Th",2.06],
    ["Pa",2.00],
    ["U" ,1.96],
    ["Np",1.9 ],
    ["Pu",1.87],
    ["Am",1.8 ],
    ["Cm",1.69],
    ["Bk",1.54],
    ["Cf",1.83],
    ["Es",1.5 ],
    ["Fm",1.5 ],
    ["Md",1.5 ],
    ["No",1.5 ],
    ["Lr",1.5 ],
    ["Rf",1.5 ],
    ["Db",1.5 ],
    ["Sg",1.5 ],
    ["Bh",1.5 ],
    ["Hs",1.5 ],
    ["Mt",1.5 ],
    ["Ds",1.5 ]
]

def EN():
    # electronegativity according to Allred & Rochow (1958)
    #Allred, A. L., & Rochow, E. G. (1958). A scale of electronegativity based on electrostatic force. Journal of Inorganic and Nuclear Chemistry, 5(4), 264-268.
    l_en=[["Li","LI",0.95,0.633,0.97]	,
          ["Na","NA",1.85,0.749,1.01]	,
          ["K","K",1.85,0.451,0.91]	,
          ["Rb","RB",1.85,0.397,0.89]	,
          ["Cs","CS",1.85,0.335,0.86]	,
          ["Be","BE",1.60,2.024,1.47]	,
          ["Mg","MG",2.50,1.344,1.23]	,
          ["Ca","CA",2.50,0.829,1.04]	,
          ["Sr","SR",2.50,0.682,0.99]	,
          ["Ba","BA",2.50,0.637,0.97]	,
          ["Sc","SC",2.65,1.280,1.20]	,
          ["Y","Y",2.65,1.015,1.11]	,
          ["La","LA",2.65,0.928,1.08]	,
          ["Ti","TI",2.80,1.597,1.32]	,
          ["V","V",2.95,1.969,1.45]	,
          ["Cr","CR",3.10,2.267,1.56]	,
          ["Mn","MN",3.25,2.382,1.60]	,
          ["Fe","FE",3.40,2.505,1.64]	,
          ["Co","CO",3.55,2.652,1.70]	,
          ["Ni","NI",3.70,2.802,1.75]	,
          ["Cu","CU",3.85,2.798,1.75]	,
          ["Ag","AG",3.35,1.868,1.42]	,
          ["Zn","ZN",4.00,2.564,1.66]	,
          ["Cd","CD",4.00,2.003,1.46]	,
          ["B","B",2.25,3.516,2.01]	,
          ["Al","AL",3.15,2.022,1.47]	,
          ["Ga","GA",4.65,3.000,1.82]	,
          ["In","IN",4.65,2.075,1.49]	,
          ["C","C",2.90,4.878,2.50]	,
          ["Si","SI",3.80,2.762,1.74]	,
          ["Ge","GE",5.30,3.543,2.02]	,
          ["Sn","SN",5.30,2.708,1.72]	,
          ["N","N",3.55,6.483,3.07]	,
          ["P","P",4.45,3.678,2.06]	,
          ["As","AS",5.95,4.064,2.20]	,
          ["Sb","SB",5.95,2.993,1.82]	,
          ["O","O",4.20,7.670,3.50]	,
          ["S","S",5.10,4.715,2.44]	,
          ["Se","SE",6.60,4.821,2.48]	,
          ["Te","TE",6.60,3.517,2.01]	,
          ["F","F",4.86,9.356,4.10]	,
          ["Cl","CL",5.75,5.820,2.83]	,
          ["Br","BR",7.25,5.559,2.74]	,
          ["I","I",7.25,4.074,2.21]	,
]
    return l_en

def ele_to_EN(ele):
## givs vdw radius for elment
    en = EN()
    ex = False
    for i in range(len(en)):
        if ele == en[i][0] or ele == en[i][1]:
            a_en = en[i][4]
            ex=True
    if ex==False:
        a_en = False
    return a_en 

def vdw_rad():
#VdW radii for all main group elmenets
#Mantina, M., Chamberlin, A. C., Valero, R., Cramer, C. J., & Truhlar, D. G. (2009). Consistent van der Waals radii for the whole main group. The Journal of Physical Chemistry A, 113(19), 5806-5812.
    rad=[["H","H",1.10],
         ["He","HE",1.40],
         ["Li","LI",1.81],
         ["Be","BE",1.53],
         ["B","B",1.92],
         ["C","C",1.70],
         ["N","N",1.55],
         ["O","O",1.52],
         ["F","F",1.47],
         ["Ne","NE",1.54],
         ["Na","NA",2.27],
         ["Mg","MG",1.73],
         ["Al","AL",1.84],
         ["Si","SI",2.10],
         ["P","P",1.80],
         ["S","S",1.80],
         ["Cl","CL",1.75],
         ["Ar","AR",1.88],
         ["K","K",2.75],
         ["Ca","CA",2.31],
         ["Ga","GA",1.87],
         ["Ge","GE",2.11],
         ["As","AS",1.85],
         ["Se","SE",1.90],
         ["Br","BR",1.83],
         ["Kr","KR",2.02],
         ["Rb","RB",3.03],
         ["Sr","SR",2.49],
         ["In","IN",1.93],
         ["Sn","SN",2.17],
         ["Sb","SB",2.06],
         ["Te","TE",2.06],
         ["I","I",1.98],
         ["Xe","XE",2.16],
         ["Cs","CS",3.43],
         ["Ba","BA",2.68],
         ["Tl","TL",1.96],
         ["Pb","PB",2.02],
         ["Bi","BI",2.07],
         ["Po","PO",1.97],
         ["At","AT",2.02],
         ["Rn","RN",2.20],
         ["Fr","FR",3.48],
         ["Ra","RA",2.83],
         ["DUM","DUM",0.00]]
    return rad

def ele_to_vdw_rad(ele):
## givs vdw radius for elment
    vdw = vdw_rad()
    r=-100
    ex = False
    for i in range(len(vdw)):
        if ele == vdw[i][0] or ele == vdw[i][1]:
            r = vdw[i][2]
            ex=True
    if ex==False:
        r = False
    return r 

def xyz_to_uvw(cell, xyz):
##converts xyz to uvw
    a=cell.a
    b=cell.b
    c=cell.c
    alpha=np.radians(cell.alpha)
    beta=np.radians(cell.beta)
    gamma=np.radians(cell.gamma)
    x=xyz[0]
    y=xyz[1]
    z=xyz[2]
    #calculate unitcell volumen
    omega=a*b*c*np.sqrt(1 - np.cos(alpha)**2 - np.cos(beta)**2 - np.cos(gamma)**2 + 2*np.cos(alpha)*np.cos(beta)*np.cos(gamma))
    #caculate fractional coordinates
    u=(1/a) *x -(np.cos(gamma)/(a*np.sin(gamma)))*y + (b*c*((np.cos(alpha)*np.cos(gamma)-np.cos(beta))/(omega*np.sin(gamma))))*z
    v=0*x + ((1)/(b*np.sin(gamma)))*y + (a*c*((np.cos(beta)*np.cos(gamma)-np.cos(alpha))/(omega*np.sin(gamma))))*z
    w= 0*x + 0*y + ((a*b*np.sin(gamma))/omega)*z 
    uvw=[np.around(u,5),np.around(v,5),np.around(w,5)]
    
    return uvw


def uvw_to_xyz(cell, uvw):
##converts xyz to uvw
    a=cell.a
    b=cell.b
    c=cell.c
    alpha=np.radians(cell.alpha)
    beta=np.radians(cell.beta)
    gamma=np.radians(cell.gamma)
    u=uvw[0]
    v=uvw[1]
    w=uvw[2]
    #calculate unitcell volume
    omega=a*b*c*np.sqrt(1 - np.cos(alpha)**2 - np.cos(beta)**2 - np.cos(gamma)**2 + 2*np.cos(alpha)*np.cos(beta)*np.cos(gamma))
    #caculate fractional coordinates
    x= a*u + (b*np.cos(gamma))*v + (c*np.cos(beta))*w
    y= 0*u + (b*np.sin(gamma))*v + (c*((np.cos(alpha)-np.cos(beta)*np.cos(gamma))/(np.sin(gamma))))*w
    z= 0*u + 0*v + (omega/(a*b*np.sin(gamma)))*w 
    uvw=[np.around(x,5),np.around(y,5),np.around(z,5)]
    
    return uvw

class Atom:
#discribes an attom read in from and *.res file
    def __init__(self,line,a_num,res_num,sfac,cell,resi_f,part):
        self.a_num=a_num
        self.res_num=res_num
        self.a_nam=line[0]
        self.cif_nam=line[0]+"_"+str(resi_f)
        self.ele=sfac[int(line[1])-1]
        self.u=float(line[2])
        self.v=float(line[3])
        self.w=float(line[4])
        self.x,self.y,self.z = uvw_to_xyz(cell,[float(line[2]),float(line[3]),float(line[4])])
        self.cov=ele_to_cov_rad(sfac[int(line[1])-1])
        if self.cov == -1.0:
            print("Did not find covalent radius! Aborting!")
            return
        self.vdw=ele_to_vdw_rad(sfac[int(line[1])-1])
        self.EN=ele_to_EN(sfac[int(line[1])-1])
        self.resi_f=resi_f
        self.cap=False
        self.part=abs(part)
#        print(len(line))
        if len(line)==9:
            self.iso="Uani"
            self.adp=[line[6],line[7],0,0,0,0]
        if len(line)==10:
            self.iso="Uani"
            self.adp=[line[6],line[7],line[8],0,0,0]
        if len(line)==7:
            self.iso="Uiso"
            self.adp=[line[6]]


class Res:
#defines one residue
    def __init__(self,line):    
        self.res_nam=line[1]
        self.res_num=int(line[2])
        self.alter=False
        self.part=[]
        self.atoms_m4=[]
        self.atoms_m3=[]
        self.atoms_m2=[]
        self.atoms_m1=[]
        self.atoms_0=[]
        self.atoms_1=[]
        self.atoms_2=[]
        self.atoms_3=[]
        self.atoms_4=[]
        self.q=0
        self.S=1

def check_if_atom(line):
    #checks if line is not startet with _
    if list(line)[0]=="_":
        return False
    return True

class Cif_atom:
    def __init__(self,line,x,y,z,label,type_symbol,Uiso,adp_type,occ,flags,symmetry,disorder_group,a_num,cell):
        self.res_num=int(line[label].split('_')[1])
        self.resi_f=int(line[label].split('_')[1])
        self.a_nam=line[label].split('_')[0]
        self.a_num=a_num
        self.cif_nam=line[label]
        self.ele=line[type_symbol]
        u=float(line[x].split('(')[0])
        v=float(line[y].split('(')[0])
        w=float(line[z].split('(')[0])
        self.cap=False
        self.u=u
        self.v=v
        self.w=w
        self.x=uvw_to_xyz(cell,[u,v,w])[0]
        self.y=uvw_to_xyz(cell,[u,v,w])[1]
        self.z=uvw_to_xyz(cell,[u,v,w])[2]
        self.org_u=line[x]
        self.org_v=line[y]
        self.org_w=line[z]
        self.iso=line[adp_type]
        self.Uiso=line[Uiso].split('(')[0]
        self.occ=line[occ]         
        self.r_flag=line[flags]
        self.s_sym=line[symmetry]
        
        self.cov=ele_to_cov_rad(line[type_symbol])
        if self.cov == -1.0:
            print("Did not find covalent radius! Aborting!")
            return
        self.vdw=ele_to_vdw_rad(line[type_symbol])
        self.EN=ele_to_EN(line[type_symbol])
        self.cap=False        
        try: 
            int(line[disorder_group])
            part=abs(int(line[disorder_group]))
        except:
            part=0
        self.part=abs(part)

class Cell:
#defines one residue
    def __init__(self):    
        self.a=0
        self.b=0
        self.c=0
        self.alpha=0
        self.beta=0
        self.gamma=0

def read_cif(cif_name):
#read CIF file in
    cif_head=[]
    cif_coord=[]
    cif_aniso=[]
    cif_sym=[]
    #res_int=[]
    read_cif = open(cif_name, "r")
    count=-1
    loop=False
    coord=False
    #aniso=False
    #bonds=False
    #angle=False
    sym=False
    a_num=0
    #cell_l=[0,0,0,0,0,0]
    cell = Cell()
    count = -1
    for line in read_cif:
        count +=1
        l_split=line.split()
        if len(l_split)==0:
            coord = False
            #aniso = False
            #bonds = False
            #angle = False
            loop = False
            sym = False
        
        elif len(l_split)>0:
            if l_split[0]=="_cell_length_a":
                cell.a=float(l_split[1].split("(")[0])
                #cell_l[0]=float(l_split[1].split("(")[0])
            if l_split[0]=="_cell_length_b":
                cell.b=float(l_split[1].split("(")[0])
                #cell_l[1]=float(l_split[1].split("(")[0])
            if l_split[0]=="_cell_length_c":
                cell.c=float(l_split[1].split("(")[0])
                #cell_l[2]=float(l_split[1].split("(")[0])
            if l_split[0]=="_cell_angle_alpha":
                cell.alpha=float(l_split[1].split("(")[0])
                #cell_l[3]=float(l_split[1].split("(")[0])
            if l_split[0]=="_cell_angle_beta":
                cell.beta=float(l_split[1].split("(")[0])
                #cell_l[4]=float(l_split[1].split("(")[0])
            if l_split[0]=="_cell_angle_gamma":
                cell.gamma=float(l_split[1].split("(")[0])
                #cell_l[5]=float(l_split[1].split("(")[0])
            if l_split[0]=="loop_":
#              print("ENTER loop !!!!!!!!!!!!!!!!!")
                count=-1
                loop = True
           
        if loop == False:
            cif_head.append(line)
        if loop == True:
            if len(l_split)>0:
#            print(l_split[0])
                if l_split[0]=="_atom_site_fract_x":
                    coord=True
                    x=count
                if l_split[0]=="_atom_site_fract_y":
                    y=count
                if l_split[0]=="_atom_site_fract_z":
                    z=count
                if l_split[0]=="_atom_site_label":
                    label=count
                if l_split[0]=="_atom_site_type_symbol":
                    type_symbol=count
                if l_split[0]=="_atom_site_U_iso_or_equiv":
                    Uiso=count
                if l_split[0]=="_atom_site_adp_type":
                    adp_type=count
                if l_split[0]=="_atom_site_occupancy":
                    occ=count
                if l_split[0]=="_atom_site_refinement_flags_posn":
                    flags=count
                if l_split[0]=="_atom_site_site_symmetry_order":
                    symmetry=count
                if l_split[0]=="_atom_site_disorder_group":
                    disorder_group=count
                if l_split[0]=="_space_group_symop_id":
                    sym=True
            if coord == True:
                check_atom=check_if_atom(l_split[0])
 #               print("check_atom",check_atom)
                if check_atom == True:
                    a_num += 1
                    atom=Cif_atom(l_split,x,y,z,label,type_symbol,Uiso,adp_type,occ,flags,symmetry,disorder_group,a_num,cell)
#                    print("atom.res_num",atom.res_num)
                    cif_coord.append(atom)

            if sym == True:
                check_atom=check_if_atom(l_split[0])
 #               print("check_atom",check_atom)
                if check_atom ==True:
                    cif_sym.append(line)
                    

    mol=cif_coord_to_mol(cif_coord)
    return cif_head,cif_coord,cif_aniso,cif_sym,cell,mol

class Res_c:
#defines one residue
    def __init__(self,res_num): 
        self.res_nam=res_num
        self.res_num=res_num
        self.alter=False
        self.part=[]
        self.atoms_m4=[]
        self.atoms_m3=[]
        self.atoms_m2=[]
        self.atoms_m1=[]
        self.atoms_0=[]
        self.atoms_1=[]
        self.atoms_2=[]
        self.atoms_3=[]
        self.atoms_4=[]
        self.q=0
        self.S=1 

def cif_coord_to_mol(atom_l):
    #create molecule with residues from cif atoms
    mol=[]
    res_num=atom_l[0].res_num
    res_l=[]
    part_l=[]
    res=[]
    alter=[]
#    print("len(atom_l)",len(atom_l))
    
    for i in range(len(atom_l)):
        if atom_l[i].res_num != res_num :
            res_num= atom_l[i].res_num
            res_l.append(res)
            part_l.append(alter)
            res=[]
            alter=[]
            
        if atom_l[i].part not in alter:
            alter.append(atom_l[i].part)
        res.append(atom_l[i])
    part_l.append(alter) 
    res_l.append(res)
#    print("####len res_l",len(res_l),len(part_l))
    
    for i in range(len(res_l)):
        res=Res_c(res_l[i][0].res_num)
        res.part=part_l[i]
        for j in range(len(res_l[i])):              
            part_name="atoms_"+str(abs(res_l[i][j].part))
            part_list=getattr(res,part_name)
            part_list.append(res_l[i][j])
#            print("type(",part_name,type(part_list))
            setattr(res,part_name,part_list)

        mol.append(res)
        
    for i in range(len(mol)):
#        print("mol[i].part",mol[i].part)
        if len(mol[i].part) > 1:
            mol[i].alter=True
        for k in range(len(mol[i].part)):
            if 0 in mol[i].part:
                if mol[i].part[k]==0:
                    continue
 #            print("TEST8¤¤¤¤¤¤¤¤¤¤¤¤")
                part_name="atoms_"+str(abs(mol[i].part[k]))
                l_frag=mol[i].atoms_0 + getattr(mol[i],part_name)
                setattr(mol[i],part_name,l_frag)
            
    return mol



def find_matching_atom(A1,cif_coord):
    #find mathing atom read in from cif
    for i in range(len(cif_coord)):
        if A1.cif_nam == cif_coord[i].cif_nam:
            return cif_coord[i]

def cif_atom_to_string_org(A):
#    creates string to print from a cif atom
    string= A.a_nam + " "
    string += A.ele + " "
    string += A.org_u + " "
    string += A.org_v + " "
    string += A.org_w + " "
    string += A.Uiso + " "
    string += A.iso + " "
    string += A.occ + " "
    string += A.r_flag + " "
    string += A.s_sym + " "
    string += str(A.part)# + "\n"
    return string


def cif_atom_to_string(A):
#    creates string to print from a cif atom
    string= A.cif_nam + " "
    string += A.ele + " "
    string += str(A.u) + " "
    string += str(A.v) + " "
    string += str(A.w) + " "
    string += A.Uiso + " "
    string += A.iso + " "
    string += A.occ + " "
    string += A.r_flag + " "
    string += A.s_sym + " "
    string += str(A.part)# + "\n"
    return string

    
def cif_cap_to_string(A):
#    creates string to print from a cif atom
    string= A.a_nam + "_c "
    string += A.ele + " "
    string += str(np.round(A.u,5)) + "(0) "
    string += str(np.round(A.v,5)) + "(0) "
    string += str(np.round(A.w,5)) + "(0) "
    string +=  "0.01 Uiso 0 R 1 .\n"
    return string
  
def write_cif(res,cif_head,cif_sym,path="",name=""):
    #writes out xyz file
    if name =="":
        name=str(res.res_num)
    #if res.part !="0":
    #    name = name +"_"+str(res.part)
    if path == "":
        output=str(name)+".cif"
    else:
        output = os.path.join(path,str(name)+".cif")
    file = open(output, "w")
    for i in range(len(cif_head)):
        string=cif_head[i]
        file.write(string)

    string='''loop_
   _space_group_symop_id
   _space_group_symop_operation_xyz 
'''
    file.write(string) 
    for i in range(len(cif_sym)):
        file.write(cif_sym[i])
    file.write("\n")

    string='''loop_
  _atom_site_label
  _atom_site_type_symbol
  _atom_site_fract_x
  _atom_site_fract_y
  _atom_site_fract_z
  _atom_site_U_iso_or_equiv
  _atom_site_adp_type
  _atom_site_occupancy
  _atom_site_refinement_flags_posn
  _atom_site_site_symmetry_order
  _atom_site_disorder_group
'''
    file.write(string) 
    for i in range(len(res.cif_atoms)):
        string=cif_atom_to_string(res.cif_atoms[i])
        file.write(string)

        file.write("\n")
    
def ele_to_cov_rad(ele):
## givs covalend radius for elment
    for i in range(len(cov_rad)):
        if ele == cov_rad[i][0]:
            return cov_rad[i][1]
    return -1

def CDist2(A,B):
#calculate distance betweenn two points
    return len3dvec(twoP_to_vec(A, B))

def len3dvec(vec):
## calculates lengh of a 3D vecor
## input as list
    return np.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)

def twoP_to_vec(A,B):
#creates vector between two points
    return np.array([B[0]-A[0], B[1]-A[1], B[2]-A[2]])

def twoA_to_vec(A1,A2):
#creates vector between two atoms
    A=[A1.x,A1.y,A1.z]
    B=[A2.x,A2.y,A2.z]
    vec = np.array([B[0]-A[0], B[1]-A[1], B[2]-A[2]])
    return vec

def norm_vec_to(vec,l):
# normalice vector to length of l
    l_org=len3dvec(vec)
    for i in range(len(vec)):
        vec[i]=(vec[i]*l)/(l_org)
    return vec

def ScalPr(x,y):
#calculate the scalar product
        pro= x[0]*y[0]+x[1]*y[1]+x[2]*y[2]
        return pro
    
def C2Angle(x,y):
#Calculates the angle between x and y
#Answer in degrees
        rtodeg = 57.2957795
        C2angle=(ScalPr(x,y)/(len3dvec(x)*len3dvec(y)))
        if C2angle == 1 :
            C2angle=0
        elif C2angle == -1:
            C2angle=180
        else:
            C2angle=np.arccos(C2angle)*rtodeg
        return C2angle

def Cross(x1,x2):
#Calculates the cross product x3 = x1 x x2
        x3 = [0,0,0] 
        x3[0]=x1[1]*x2[2]-x2[1]*x1[2]
        x3[1]=x1[2]*x2[0]-x2[2]*x1[0]
        x3[2]=x1[0]*x2[1]-x2[0]*x1[1]
        return x3

def CDihed(x,y,z,w):
#Calculate the dihedral angle x-y-z-w
#Answer in degrees between -180 and +180
        #Set v1=y-x, v2=z-y, v3=w-z
        v1=[0,0,0]
        v2=[0,0,0]
        v3=[0,0,0]
        for i in range(3):
            v1[i]=y[i]-x[i]
            v2[i]=z[i]-y[i]
            v3[i]=w[i]-z[i]

        #Calculate the normal vectors n1 and n2
        n1=Cross(v1,v2)
        n2=Cross(v2,v3)
        
        #Calculate the torsion angle;
        #The sign is determined by the sign of v1.n2
        CDihed=C2Angle(n1,n2)
        if ScalPr(v1,n2) < 0:
                CDihed=-CDihed
        return  CDihed

def atom_dist(A1,A2):
# calculate distance beetween two atoms
    C1=[A1.x,A1.y,A1.z]
    C2=[A2.x,A2.y,A2.z]
    dist=CDist2(C1,C2)
    return dist

def find_first_shell(mol,res,anum,part,l_frag,cap1):
#    finds first bonded atoms from neighbouring residues
    anums=[]
    count=0
    radius_tolerance = float(OV.GetParam('snum.NoSpherA2.frag_HAR.radius_tolerance'))
#   A1=[mol[res][anum].x,mol[res][i].y,mol[res][i].z]
    for i in range(len(mol)):
        if i != res:
            if mol[i].alter != True:
                l_res= mol[i].atoms_0 +mol[i].atoms_1 + mol[i].atoms_m1
            elif part in mol[i].part:
                if int(part)==0:
                    part=1
                part_name="atoms_"+str(part)
                l_res=getattr(mol[i],part_name)  
            else:
                l_res= mol[i].atoms_0 +mol[i].atoms_1 + mol[i].atoms_m1
#            print(l_frag[anum].res_num)
#            print_atom(l_frag[anum])
            for k in range(len(l_res)):
                dist=atom_dist(l_frag[anum],l_res[k])
                if dist <= (l_frag[anum].cov+l_res[k].cov+radius_tolerance):
#                    print("A_NAM", mol[i][k].a_nam, "addet to res",mol[res][anum].res_num)
                    atom_ex=False
                    for l in range(len(cap1)):
                        if are_atoms_eaqual(l_res[k],cap1[l])==True:
                            atom_ex=True
                    for l in range(len(anums)):
                        if are_atoms_eaqual(l_res[k],anums[l])==True:
                            atom_ex=True
                        
                    if atom_ex==False:    
                        add=copy.deepcopy(l_res[k])
                        add.cap=True
                        count +=1
                        add.a_nam = add.a_nam + "_1C"+str(count)
                        anums.append(add)        
#                        print("TEST1######################",mol[i].res_num)
    return anums

def print_atom(a):
    #print out atom information
    print(a.a_nam,a.ele,a.res_num,a.a_num)    

def find_second_shell(mol,cap1,res,part,cap2,hbond_ex, minHbond):
#    finds second bonded atoms from neighbouring residues
    anums=[]
 #   print("cap1cap1cap1",cap1)
 #   A1=[mol[res][anum].x,mol[res][i].y,mol[res][i].z]
    count=0
    radius_tolerance = float(OV.GetParam('snum.NoSpherA2.frag_HAR.radius_tolerance'))
    for j in range(len(cap1)):
        for i in range(len(mol)):

            if i != res:
#            print("====find caps2 for res",res+1, "in res",i+1)
                if mol[i].alter != True:
                    l_res= mol[i].atoms_0 + mol[i].atoms_1 + mol[i].atoms_m1
                elif part in mol[i].part:
                    if int(part) == 0:
                        part = 1
                    part_name = "atoms_"+str(part)
                    l_res = getattr(mol[i],part_name)  
            else:
                ### I THINK THIS IS WHERE THINGS ARE GOING WRONG; BUT IF I DO NOT CONTINUE I HAVE DOUBLED ATOMS
                continue
                l_res = mol[i].atoms_0 + mol[i].atoms_1 + mol[i].atoms_m1
            for k in range(len(l_res)):
#                if cap1[j].res_num == l_res[k].res_num:
#                  if l_res[k].part=="0" or l_res[k].part==part:  
                dist = atom_dist(cap1[j],l_res[k])
                if 0.5 < dist <= (cap1[j].cov+l_res[k].cov+radius_tolerance):
                    atom_ex=False
                    for l in range(len(cap1)):
                        if are_atoms_eaqual(l_res[k],cap1[l]) == True:
                            atom_ex=True
                    for l in range(len(cap2)):
                        if are_atoms_eaqual(l_res[k],cap2[l]) == True:
                            atom_ex=True
                    for l in range(len(anums)):
                        if are_atoms_eaqual(l_res[k],anums[l]) == True:
                            atom_ex=True

                    if atom_ex==False:
#                        print("TEST2######################",mol[i].res_num)
                        add=copy.deepcopy(l_res[k])
                    
                        add.cap=True
                        count +=1
                        add.a_nam = add.a_nam + "_2C"+str(count)
                        anums.append(add)
#                        if hbond_ex==True or minHbond==True :
#                            plan,plan_atoms = check_if_plan(add,l_res)
#                            if plan == True:
#                                for l in range(len(plan_atoms)):
#                                    for u in range(len(cap1)):
#                                        if are_atoms_eaqual(plan_atoms[l],cap1[i])==False:
#                                            anums.append(plan_atoms[i])
#                           ring=check_in_ring(add,l_res)
#                        print_atom(add)
                    
    return anums 


def check_if_plan(atom,res):
    #check if  atom is planar
    
    plan=False
    n_atom=[]
    radius_tolerance = float(OV.GetParam('snum.NoSpherA2.frag_HAR.radius_tolerance'))
    for i in range(len(res)):
        dist=atom_dist(atom,res[i])
        if 0.5 <  dist <= (atom.cov + res[i].cov+radius_tolerance):
#            if are_atoms_eaqual(cap1,res[i]) == False:
                n_atom.append(res[i])
    if len(n_atom)==3:
        
        a1= atom_to_coord(atom)
        a2= atom_to_coord(n_atom[0])
        a3= atom_to_coord(n_atom[1])
        a4= atom_to_coord(n_atom[2])
        dih=CDihed(a1,a2,a3,a4)
        print("check plan",atom.res_num,np.round(dih,2))
        
        if -2 < dih <2 or dih < -178 or 178 < dih:
            print("atom is planar")
            plan = True
        
    
    return plan, n_atom

def atom_to_coord(A):
    #transfomres class atom to list coord
    coord=[A.x,A.y,A.z]
    return coord

def find_junction(mol,cap2,cap1,cell,res,part):
    print("Start to find junctions for res",res+1,"part",part)
#    finds second bondet atoms from naibouring residues
    anums=[]
    j_num=1
    elongate = []
    atom_j=[]
    radius_tolerance = float(OV.GetParam('snum.NoSpherA2.frag_HAR.radius_tolerance'))
    for j in range(len(cap2)):
 #     continue
        if cap2[j].ele!= "H":  ##NEW
            for i in range(len(mol)):
                if i != res:
#                 print("serching vor junctions for res",res,"in residue",i)
                    if mol[i].alter != True:
                        l_res= mol[i].atoms_0 +mol[i].atoms_1 + mol[i].atoms_m1
#                      print("alter is not true", len(l_res))
                    elif part in mol[i].part:
                        if int(part)==0:
                            part1 =1
                        else:
                            part1 = part
                        part_name="atoms_"+str(part1)
                        l_res=getattr(mol[i],part_name)  
#                      print("alter is true and equal", len(l_res))
                    else:
                        l_res= mol[i].atoms_0 +mol[i].atoms_1 + mol[i].atoms_m1
                        print("alter is true and NOT equal", len(l_res))
                     
                    for k in range(len(l_res)):         
                        dist=atom_dist(cap2[j],l_res[k])
                        if 0.5 <  dist <= (cap2[j].cov + l_res[k].cov+radius_tolerance):
                            real1=False
                            real2=False
                            for l in range(len(cap1)):
                                if are_atoms_eaqual(l_res[k],cap1[l])==True:
                                    real1=True
                            for l in range(len(cap2)):
                                if are_atoms_eaqual(l_res[k],cap2[l])==True:
                                    real2=True
                
                            if real1==False and real2==False:
                                BO=bond_order(cap2[j], l_res[k])
#                                print("The bond order is " ,BO)
                                j_atom=copy.deepcopy(l_res[k])
                                atom_j.append(copy.deepcopy(l_res[k]))
                                abc=1
                                if abc==2:
                                    abc=1
                                if BO > 1 :
                                    print(j_atom.cif_nam, "is addet to cap 2")
                                    elongate.append(j_atom)
                                else:
                                    j_nam="H_j"+str(j_num)
                                    j_num += 1
                                    
                                    j_atom.a_nam=j_nam
                                    j_atom.ele="H"
                                    j_atom.cov=ele_to_cov_rad(j_atom.ele)
                                    j_atom.vdw=ele_to_vdw_rad(j_atom.ele)
                                    j_atom.EN=ele_to_EN(j_atom.ele)
                                    j_atom.cap=True
                                    j_atom = junc_pos(cap2[j],j_atom,cell)
                                    atom_ex=False
                                    for l in range(len(anums)):
                                        if are_atoms_eaqual(j_atom,anums[l])==True:
                                            atom_ex=True
                                    if atom_ex==False:
                                        anums.append(j_atom)
    if len(atom_j)>=2:
        for i in range(0,len(atom_j)-1):
            for k in range(i+1,len(atom_j)):
                if are_atoms_eaqual(atom_j[i],atom_j[k])==True:
                    elongate.append(atom_j[i])
                
 #   print("anums , elongate",len(anums) , len(elongate))                
    return anums , elongate

def bond_order(A1,A2):
    #defines bond order like Blom & Haaland (1985) as used in invariomtool
    # Blom, R., & Haaland, A. (1985). A modification of the schomaker & stevenson rule for prediction of single bond distances. Journal of molecular structure, 128(1-3), 21-27.
    rc1=A1.cov
    en1=A1.EN
    rc2=A2.cov
    en2=A2.EN
    if rc1 != False and en1 != False and rc2 != False and en2 != False:
        dist=atom_dist(A1, A2)
        x=(rc1+rc2-0.08*abs(en1-en2))-dist
    else:
        x=0
    if x <= 0.09:
        bo = 1
    elif 0.09 < x < 0.183:
#    elif 0.09 < x < 0.17:
        bo = 1.5
    elif 0.183 <= x <= 0.27:
#    elif 0.17 <= x <= 0.27:
        bo = 2
    else:#0.27 < x
        bo = 3 
    return bo

def junc_pos(AC2,AJ,cell):
#sets coordinates for the juction atoms
    v1 = twoA_to_vec(AC2,AJ)    
    v2 = norm_vec_to(v1,1.094)
    AJ.x=np.around(AC2.x+v2[0],5)
    AJ.y=np.around(AC2.y+v2[1],5)
    AJ.z=np.around(AC2.z+v2[2],5)
    AJ.u=np.around(xyz_to_uvw(cell,[AJ.x,AJ.y,AJ.z])[0],5)
    AJ.v=np.around(xyz_to_uvw(cell,[AJ.x,AJ.y,AJ.z])[1],5)
    AJ.w=np.around(xyz_to_uvw(cell,[AJ.x,AJ.y,AJ.z])[2],5)
    return AJ

def are_atoms_eaqual(A1,A2):
##    checks if atoms are qual
    return (A1.x==A2.x and A1.y==A2.y and A1.z==A2.z)

def build_cap(mol,res,cell,part):
#builds caps for residues
    frag=[]
    cap=[]
    cap1=[]
    cap2=[]
    frag_core=[]
    hbond_ex=OV.GetParam('snum.NoSpherA2.frag_HAR.H_box_ex')
    minHbond=OV.GetParam('snum.NoSpherA2.frag_HAR.min_H_bond')
    print("minHbond!!!!!!!!!!!!!!!!!!!!!",minHbond)
    print("hbond_ex!!!!!!!!!!!!!!!!!!!!!",hbond_ex)
    l_frag=[]
    part_name="atoms_"+str(abs(part))
    l_frag=getattr(mol[res],part_name)
    for i in range(len(l_frag)):

        atom=copy.deepcopy(l_frag[i])
        frag.append(atom)
        frag_core.append(copy.deepcopy(l_frag[i]))
        if hbond_ex==True:#NEW
            bond_l=find_hbond(mol,res,i,part,l_frag)
            if len(bond_l) >=1:
                for k in range(len(bond_l)):
                    cap1.append(bond_l[k])
            print("Hydrogen bonds are getting cappend",l_frag[i].res_num,len(cap1))
        shell1=find_first_shell(mol,res,i,part,l_frag,cap1)
#        print("number of atoms in the fist shell for fragment",mol[res].res_num,len(shell1))
        if len(shell1)>=1:
            for k in range(len(shell1)):
                cap1.append(shell1[k])
    shell2=find_second_shell(mol,cap1,res,part,cap2,hbond_ex, minHbond)
    if len(shell2)>=1:
        for k in range(len(shell2)):
            cap2.append(shell2[k])
    if minHbond==True:
#        print("small Hbond cap1!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        for h in range(len(l_frag)):
            bond_min=find_hbond(mol,res,h,part,l_frag)
 #           print("len(bind_l)",len(bond_min))
            if len(bond_min) > 0:
#                print("small Hbond cap!&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&!!!")
                for k in range(len(bond_min)):
                    cap2.append(bond_min[k])
        
 #   print("START to find caps for res",res,"part",part)
    junc1, elongate = find_junction(mol,cap2,cap1,cell,res,part)##NEW
    if len(elongate) >= 1:##NEW
        for u in range(5):##NEW
           #print("cycle of elongate cap atoms########################################",res,u,len(elongate))
            for k in range(len(elongate)):##NEW
                cap2.append(elongate[k])##NEW
                junc1, elongate = find_junction(mol,cap2,cap1,cell,res,part)##NEW
                if len(elongate)==0 :
                    break

    for i in range(len(cap1)):
        frag.append(cap1[i])
        cap.append(cap1[i])
    for i in range(len(cap2)):
        frag.append(cap2[i])
        cap.append(cap2[i])
    for i in range(len(junc1)):
        frag.append(junc1[i])
        cap.append(junc1[i])

    return frag,cap,frag_core

def find_hbond(mol,res,anum,part,l_frag):##NEW
#    finds first bondet atoms from naibouring residues
    anums=[]
    count=0
    if  l_frag[anum].ele == "H":
        for i in range(len(mol)):
            if mol[i].alter != True:
                l_res= mol[i].atoms_0 +mol[i].atoms_1 + mol[i].atoms_m1
            elif part in mol[i].part:
                part_name="atoms_"+str(part)
                l_res=getattr(mol[i],part_name)  
            else:
                l_res= mol[i].atoms_0 +mol[i].atoms_1 + mol[i].atoms_m1
              
            for k in range(len(l_res)):
                if l_frag[anum].res_num != l_res[k].res_num:
                    if l_res[k].ele == "O" or l_res[k].ele == "N": 
                        dist=atom_dist(l_frag[anum],l_res[k])
                        vdw1=ele_to_vdw_rad(l_frag[anum].ele)
                        vdw2=ele_to_vdw_rad(l_res[k].ele)
                        if vdw2 != False:
                            if dist <= (vdw1+vdw2-0.4):
                                add=copy.deepcopy(l_res[k])
                                add.cap=True
                                count +=1
                                add.a_nam = add.a_nam + "_1H"+str(count)
                                anums.append(add)            
    return anums

def build_fragments(mol,cell):
#   build up capped fragments with the MFCC capping sheme
    frag_l=[]
    for i in range(len(mol)):
        mol[i].part.sort()
        
        if mol[i].alter != True :
            p0=0
        elif  0 not in mol[i].part:
            p0=0
        else:
            p0=1
        for k in range(p0,len(mol[i].part)):
            frag,cap,core=build_cap(mol,i,cell,mol[i].part[k])              
            frag_l.append(Frag(mol[i].res_nam,mol[i].res_num,mol[i].part[k],frag,cap,core,mol[i].q,mol[i].S))
        
    return frag_l

class Frag:
#defines one residue
    def __init__(self,res_nam,res_num,part,atoms,cap,core,q,s):    
        self.res_nam=res_nam
        self.res_num=res_num
        self.part=abs(part)
        self.atoms_core=core
        self.atoms=atoms
        self.cap=cap
        self.q=q
        self.s=s
        self.cif_atoms=core

def write_xyz(res,path="",part=0,name=""):
    #writes out xyz file
    if name == "":
        name=str(res.res_num)
    if path == "":
        output=str(name)+".xyz"
    else:
        output=os.path.join(path,str(name+".xyz"))
    file = open(output, "w")
    file.write(str(len(res.atoms))+"\nXYZ file written during fragHAR handling of fragments! q:"+str(res.q)+" S:"+str(res.s)+" \n")
    for i in range(len(res.atoms)):
        string = str(res.atoms[i].ele)+" "+str(res.atoms[i].x)+" "+str(res.atoms[i].y)+" "+str(res.atoms[i].z)+"\n"
        file.write(string)
    file.close()

def read_qS(file,mol):
    #read in file with charge and multiplisity
    #in_list=False
    if os.path.exists(file):
        for line in open(file, "r"):
            l_split=line.split()
            if l_split == []:
                pass
            if len(l_split)>0:
                for i in range(len(mol)):
                    if int(l_split[0])==mol[i].res_num:
                        q=l_split[1]
                        mol[i].q=q
                        if len(l_split) < 3:
                            s=1
                        else:
                            s=l_split[2]
                        mol[i].S=s
                        #in_list=True
        
    for i in range(len(mol)):
        print("mol %d resnum %d: q=%d S=%d"%(i,mol[i].res_num,int(mol[i].q),int(mol[i].S)))
    return mol

def are_atoms_match_cif(A1,A2):
#   checks if atoms are qual
    equal=False
    diff = abs(A1.x-A2.x) + abs(A1.y-A2.y) + abs(A1.z-A2.z)
    if diff <= 0.01 :
        if int(A1.part)==int(A2.part):
            equal=True
    
    return equal

def add_cif_atoms(frag,cif,cell):
    #adds cif atoms to each fragment 
    for i in range(len(frag)):
        for j in range(len(frag[i].atoms_core)):
            for k in range(len(cif)):
                A1 = frag[i].atoms_core[j]
                A2 = cif[k]
                if are_atoms_match_cif(A1,A2)==True:
                    frag[i].cif_atoms.append(A2)
        if len(frag[i].atoms_core) != len(frag[i].cif_atoms):
            print("cif atoms are missingin residue ",frag[i].res_num,len(frag[i].atoms_core),len(frag[i].cif_atoms))
        
    return frag

def run_frag_HAR_wfn(input_res,input_cif,input_qS, wfn_object, part):
    import shutil
    test_frag=OV.GetParam('snum.NoSpherA2.frag_HAR.H_test')
    #print("test_frag",test_frag)
 #   test_frag=False
#    print_frag=True
    import time
    t1 = time.time()
    cif_head,cif_coord,cif_aniso,cif_sym,cell,mol=read_cif(input_cif)
    mol = read_qS(input_qS,mol)
    print("size of mol: ",len(mol))
   
    frag = build_fragments(mol,cell) 
#    if print_frag==True:
#       print("fragmenttation test is running")
#       return
    
    work_folder = wfn_object.full_dir
    wfns = []
    cifs = []
    groups = []
    hkl_fn = os.path.join(work_folder,wfn_object.name+".hkl")
    t2 = time.time()
    for i in range(len(frag)):
        path = os.path.join(OV.FilePath(),work_folder,"residue_"+str(i+1))
        if os.path.exists(path) == False:
            os.mkdir(path)
        write_xyz(frag[i],path=path,name=wfn_object.name)
        write_cif(frag[i],cif_head,cif_sym,path=path,name=wfn_object.name)
        if test_frag==True:
            print("no furhter calculation")
            continue
        
        wfn_object.full_dir = path
        wfn_object.write_orca_input(False,charge=str(frag[i].q),mult=str(frag[i].s))
        try:
            wfn_object.run(part)
        except NameError as error:
            print("The following error occured during QM Calculation # %d: "%i,error)
            OV.SetVar('NoSpherA2-Error',error)
            raise NameError('Unsuccesfull Wavefunction Calculation!')
        
        base_name = os.path.join(path,wfn_object.name)
        if os.path.exists(base_name+".wfx"):
            wfn_fn = base_name+".wfx"
        elif os.path.exists(base_name+".wfn"):
            wfn_fn = base_name+".wfn"
        wfns.append(wfn_fn)
        if int(frag[i].part) != 0:
            groups.append([0,int(frag[i].part)])
        else:
            groups.append([0])
        cifs.append(os.path.join(path,wfn_object.name+".cif"))
    from .NoSpherA2 import multi_CIF_NoSpherA2_tsc
    t3 = time.time()
    multi_CIF_NoSpherA2_tsc(cifs,hkl_fn,groups,wfns)
    try:
        shutil.move("experimental.tsc",wfn_object.name+".tsc")
    except:
        print("Error trying to move the tsc file! Make sure the calculation worked!")
        return
    OV.SetParam('snum.NoSpherA2.file',wfn_object.name+".tsc")
    t4 = time.time()
    print("-- " + "{:8.3f}".format(t2-t1) + " for fragmentation")
    print("-- " + "{:8.3f}".format(t3-t2) + " for wavefunctions")
    print("-- " + "{:8.3f}".format(t4-t3) + " for partitioning")       
