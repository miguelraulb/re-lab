# Copyright (C) 2007,2010,2011	Valek Filippov (frob@df.ru)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 or later of the GNU General Public
# License as published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA
#

import sys,struct,gtk,gobject,zlib
from utils import *

fill_types = {0:"Transparency",1:"Solid",2:"Gradient"}
clr_models = {0:"Invalid",1:"Pantone",2:"CMYK",3:"CMYK255",4:"CMY", 5:"RGB",
							6:"HSB",7:"HLS",8:"BW",9:"Gray",10:"YIQ255",11:"LAB",12:'Unknown0xc',
							13:'Unknown0xd',14:'Unknown0xe',15:'Unknown0xf',16:'Unknown0x10',
							17:'CMYK255',18:'Unknown0x12',19:'Unknown0x13',20:'Registration Color'}

bmp_clr_models = ('Invalid', 'RGB', 'CMY', 'CMYK255', 'HSB', 'Gray', 'Mono',
								'HLS', 'PAL8', 'Unknown9', 'RGB', 'LAB')
outl_corn_type =('Normal', 'Rounded', 'Cant')
outl_caps_type =('Normal', 'Rounded', 'Out Square')
fild_pal_type = {0:'Transparent', 1:'Solid', 2:'Gradient',6:'Postscript',7:'Pattern', 0xb:'Texture'} # FIXME! names are guessed by frob
fild_grad_type = ('Unknown', 'Linear', 'Radial', 'Conical', 'Squared') #FIXME! gussed

def arrw (hd, size, data):
	add_iter (hd,"Arrow ID","%02x"%struct.unpack('<I', data[0:4])[0],0,4,"<I")
	add_iter (hd,"???","%02x"%struct.unpack('<I', data[4:8])[0],4,4,"<I")
	pnum = struct.unpack('<H', data[8:10])[0]
	add_iter (hd,"#ofPts","%02x"%pnum,8,2,"<H")
	coff = 8+struct.unpack('<I', data[10:14])[0]
	add_iter (hd,"Pnt Types","",14,pnum,"txt")
	for i in range (pnum):
		x = struct.unpack('<l', data[coff+i*8:coff+4+i*8])[0]
		y = struct.unpack('<l', data[coff+4+i*8:coff+8+i*8])[0]
		Type = ord(data[14+i])
		NodeType = ''
		# FIXME! Lazy to learn dictionary right now, will fix later
		if Type&2 == 2:
			NodeType = '    Char. start'
		if Type&4 == 4:
			NodeType = NodeType+'  Can modify'
		if Type&8 == 8:
			NodeType = NodeType+'  Closed path'
		if Type&0x10 == 0 and Type&0x20 == 0:
			NodeType = NodeType+'  Discontinued'
		if Type&0x10 == 0x10:
			NodeType = NodeType+'  Smooth'
		if Type&0x20 == 0x20:
			NodeType = NodeType+'  Symmetric'
		if Type&0x40 == 0 and Type&0x80 == 0:
			NodeType = NodeType+'  START'
		if Type&0x40 == 0x40 and Type&0x80 == 0:
			NodeType = NodeType+'  Line'
		if Type&0x40 == 0 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Curve'
		if Type&0x40 == 0x40 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Arc'
		add_iter (hd,"X%u/Y%u/Type"%(i+1,i+1),"%u/%u mm"%(round(x/10000.0,2),round(y/10000.0,2))+NodeType,coff+i*8,8,"txt")

def bbox (hd,size,data):
	offset = 0
	for i in range(2):
		varX = struct.unpack('<l', data[offset+i*8:offset+4+i*8])[0]
		varY = struct.unpack('<l', data[offset+4+i*8:offset+8+i*8])[0]
		add_iter (hd,"X%u/Y%u"%(i,i),"%u/%u mm"%(round(varX/10000.0,2),round(varY/10000.0,2)),offset+i*8,8,"txt")

def obbx (hd,size,data):
	offset = 0
	for i in range(4):
		varX = struct.unpack('<l', data[offset+i*8:offset+4+i*8])[0]
		varY = struct.unpack('<l', data[offset+4+i*8:offset+8+i*8])[0]
		add_iter (hd,"X%u/Y%u"%(i,i),"%u/%u mm"%(round(varX/10000.0,2),round(varY/10000.0,2)),offset+i*8,8,"txt")

def clr_model(hd,data,offset):
	cmid = struct.unpack('<H', data[offset:offset+2])[0]
	cmod = "%02x  "%cmid
	if clr_models.has_key(cmid):
		cmod += clr_models[cmid]
	add_iter (hd,"Color Model",cmod,offset,2,"txt")
	clr = "#%02x%02x%02x%02x"%(ord(data[offset+8]),ord(data[offset+9]),ord(data[offset+10]),ord(data[offset+11]))
	add_iter (hd,"  Color",clr,offset+8,4,"txt")

def outl (hd,size,data):
	add_iter (hd,"Outline ID","%02x"%struct.unpack('<I', data[0:4])[0],0,4,"<I")
	add_iter (hd,"Line Type","%02x"%struct.unpack('<H', data[4:6])[0],4,2,"<H")
	add_iter (hd,"Caps Type","%02x"%struct.unpack('<H', data[6:8])[0],6,2,"<H")
	add_iter (hd,"???? ","%02x"%struct.unpack('<H', data[8:0xa])[0],8,2,"<H")
	add_iter (hd,"LineWidth","%.2f mm"%round(struct.unpack('<I', data[12:16])[0]/10000.0,2),12,4,"<I")

	add_iter (hd, "?? x0", "%u"%(struct.unpack('<d', data[16:24])[0]/10000),16,8,"<d")
	add_iter (hd, "?? y0", "%u"%(struct.unpack('<d', data[40:48])[0]/10000),40,8,"<d")
	for i in (0,1,3,4):                     
		var = struct.unpack('<d', data[24+i*8:32+i*8])[0]
		add_iter (hd, "?? var%d"%(i+1), "%f"%var,24+i*8,8,"<d")
	clr_model(hd,data,0x4c)
	dnum = struct.unpack('<H', data[0x68:0x6a])[0]
	add_iter (hd,"Dash num","%02x"%(dnum/2),0x68,2,"<H")
	for i in range(dnum/2):
		add_iter (hd," Dash/Space","%02x/%02x"%(struct.unpack('<H', data[0x6a+i*4:0x6c+i*4])[0],struct.unpack('<H',data[0x6c+i*4:0x6e+i*4])[0]),0x6a+i*4,4,"txt")
	add_iter (hd,"StartArrow ID","%02x"%struct.unpack('<I', data[0x80:0x84])[0],0x80,4,"<I")
	add_iter (hd,"EndArrow ID","%02x"%struct.unpack('<I', data[0x84:0x88])[0],0x84,4,"<I")


def fild (hd,size,data):
	add_iter (hd,"Fill ID","%02x"%struct.unpack('<I', data[0:4])[0],0,4,"<I")
	fill_type = struct.unpack('<h', data[4:6])[0]
	ft_txt = "%d"%fill_type
	if fill_types.has_key(fill_type):
		ft_txt += " "+fill_types[fill_type]
	add_iter (hd,"Fill Type", ft_txt,4,2,"txt")
	if fill_type > 0 and fill_type != 7:
		clr_model = struct.unpack('<h', data[8:0xa])[0]
		clrm_txt = "%d"%clr_model
		if clr_models.has_key(clr_model):
			clrm_txt += " " + clr_models[clr_model]
		add_iter (hd, "Color Model", clrm_txt,8,2,"txt")
		if fill_type == 1:
			add_iter (hd, "Color", "%02x"%struct.unpack('<i', data[0x10:0x14])[0],0x10,4,"<i")

		if fill_type == 2:
			grd_offset = 0x8
			rot_offset = 0x20
			mid_offset = 0x32
			pal_len = 16
			pal_off = 0
			prcnt_off = 0
			if hd.version >= 13:
				grd_offset = 0x16
				mid_offset = 0x3c
				pal_len = 24
				pal_off = 3
				prcnt_off = 8
			grdmode = ord(data[grd_offset])
			midpoint = ord(data[mid_offset])
			pal_num = ord(data[mid_offset+2])								
			rot = struct.unpack('<L', data[rot_offset:rot_offset+4])[0]

			if grdmode < len(fild_grad_type):
				gr_type = "%s"%fild_grad_type[grdmode]
			else:
				gr_type = "Unknown (%X)"%clrmode
			add_iter (hd, "Gradient type",gr_type, grd_offset,1,"B")
			add_iter (hd, "Rotation",rot/1000000, rot_offset,4,"<L")
			add_iter (hd, "Midpoint",midpoint, mid_offset,1,"B")

			for i in range(pal_num):
				clrmode = ord(data[mid_offset+6+pal_off+i*pal_len])
																# RGB           CMYK
				col0=ord(data[mid_offset+14+pal_off+i*pal_len])          #       BB              CC
				col1=ord(data[mid_offset+15+pal_off+i*pal_len])          #       GG              MM
				col2=ord(data[mid_offset+16+pal_off+i*pal_len])          #       RR              YY
				col3=ord(data[mid_offset+17+pal_off+i*pal_len])          #       ??              KK
				prcnt = ord(data[mid_offset+18+prcnt_off+i*pal_len])
				add_iter (hd, "Color:","%02x %02x %02x %02x\t%u"%(col0,col1,col2,col3,prcnt),mid_offset+14+pal_off+i*pal_len,5,"txt")
	elif fild_type == 7:
		add_iter (hd,"Pattern ID", struct.unpack('<I', data[8:12])[0],8,4,"txt")
		# Colors (model + color) started at 0x1c and 0x28

def bmpf (hd,size,data):
	add_iter (hd,"Pattern ID", struct.unpack('<I', data[0:4])[0],0,4,"txt")

def bmp (hd,size,data):
	add_iter (hd,"Image ID", struct.unpack('<I', data[0:4])[0],0,4,"txt")

def ftil (hd,size,data):
	for i in range(6):
		[var] = struct.unpack('<d', data[i*8:i*8+8]) 
		add_iter(hd,'Var%d'%i,var,i*8,8,"<d")

def loda_outl (hd,data,offset,l_type):
	add_iter (hd, "[000a] Outl ID",d2hex(data[offset:offset+4]),offset,4,"txt")

def loda_fild (hd,data,offset,l_type):
	add_iter (hd, "[0014] Fild ID",d2hex(data[offset:offset+4]),offset,4,"txt")

def loda_trfd (hd,data,offset,l_type):
	add_iter (hd, "[0064] Trfd ID",d2hex(data[offset:offset+4]),offset,4,"txt")

def loda_stlt (hd,data,offset,l_type):
	add_iter (hd, "[00c8] Stlt ID",d2hex(data[offset:offset+4]),offset,4,"txt")

def loda_rot(hd,data,offset,l_type):
	rot = struct.unpack('<l', data[offset:offset+4])[0]
	add_iter (hd, "[2efe] Rotate","%u"%round(rot/1000000.0,2),offset,4,"txt")

def loda_rot_center (hd,data,offset,l_type):
	rotX = struct.unpack('<l', data[offset:offset+4])[0]
	rotY = struct.unpack('<l', data[offset+4:offset+8])[0]
	add_iter (hd, "[0028] RotCenter X/Y","%u/%u"%(round(rotX/10000.0,2),round(rotY/10000.0,2)),offset,8,"txt")

def loda_name(hd,data,offset,l_type):
	if hd.version > 11:
		layrname = unicode(data[offset:],'utf-16')
	else:
		layrname = data[offset:]
	add_iter (hd,"[03e8] Layer name",layrname,offset,len(data[offset:]),"txt")

def loda_polygon (hd,data,offset,l_type):
	num = struct.unpack('<L', data[offset+4:offset+8])[0]
	add_iter (hd,"[2af8] # of angles",num,offset+4,4,"<I")
	num = struct.unpack('<L', data[offset+8:offset+0xc])[0]
	add_iter (hd,"[2af8] next point?",num,offset+8,4,"<I")
	var = struct.unpack('<d', data[offset+0x10:offset+0x10+8])[0]
	add_iter (hd,"[2af8] var1 ?",var,offset+0x10,8,"<d")
	var = struct.unpack('<d', data[offset+0x18:offset+0x18+8])[0]
	add_iter (hd,"[2af8] var2 ?",var,offset+0x18,8,"<d")
	
	for i in range(2):
		varX = struct.unpack('<l', data[offset+0x18+8+i*8:offset+0x1c+8+i*8])[0]
		varY = struct.unpack('<l', data[offset+0x1c+8+i*8:offset+0x20+8+i*8])[0]
		add_iter (hd,"[2af8] X%u/Y%u"%(i,i),"%u/%u mm"%(round(varX/10000.0,2),round(varY/10000.0,2)),offset+0x18+8+i*8,8,"txt")

def loda_coords124 (hd,data,offset,l_type):
# rectangle or ellipse or text
	x1 = struct.unpack('<l', data[offset:offset+4])[0]
	y1 = struct.unpack('<l', data[offset+4:offset+8])[0]
	add_iter (hd,"[001e] x1/y1","%u/%u mm"%(round(x1/10000.0,2),round(y1/10000.0,2)),offset,8,"txt")

	if l_type == 1:
		R1 = struct.unpack('<L', data[offset+8:offset+12])[0]
		R2 = struct.unpack('<L', data[offset+12:offset+16])[0]
		R3 = struct.unpack('<L', data[offset+16:offset+20])[0]
		R4 = struct.unpack('<L', data[offset+20:offset+24])[0]
		add_iter (hd,"[001e] R1 R2 R3 R4","%u %u %u %u mm"%(round(R1/10000.0,2),round(R2/10000.0,2),round(R3/10000.0,2),round(R4/10000.0,2)),offset+8,16,"txt")

	if l_type == 2:
		a1 = struct.unpack('<L', data[offset+8:offset+12])[0]
		a2 = struct.unpack('<L', data[offset+12:offset+16])[0]
		a3 = struct.unpack('<L', data[offset+16:offset+20])[0]
		add_iter (hd,"[001e] Start/End Rot angles; Pie flag","%u %u %u"%(round(a1/1000000.0,2),round(a2/1000000.0,2),round(a3/1000000.0,2)),offset+8,12,"txt")

def loda_coords3 (hd,data,offset,l_type):
	pointnum = struct.unpack('<L', data[offset:offset+4])[0]
	for i in range (pointnum):
		x = struct.unpack('<l', data[offset+4+i*8:offset+8+i*8])[0]
		y = struct.unpack('<l', data[offset+8+i*8:offset+12+i*8])[0]
		Type = ord(data[offset+4+pointnum*8+i])
		NodeType = ''
		# FIXME! Lazy to learn dictionary right now, will fix later
		if Type&2 == 2:
			NodeType = '    Char. start'
		if Type&4 == 4:
			NodeType = NodeType+'  Can modify'
		if Type&8 == 8:
			NodeType = NodeType+'  Closed path'
		if Type&0x10 == 0 and Type&0x20 == 0:
			NodeType = NodeType+'  Discontinued'
		if Type&0x10 == 0x10:
			NodeType = NodeType+'  Smooth'
		if Type&0x20 == 0x20:
			NodeType = NodeType+'  Symmetric'
		if Type&0x40 == 0 and Type&0x80 == 0:
			NodeType = NodeType+'  START'
		if Type&0x40 == 0x40 and Type&0x80 == 0:
			NodeType = NodeType+'  Line'
		if Type&0x40 == 0 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Curve'
		if Type&0x40 == 0x40 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Arc'
		add_iter (hd,"[001e] X%u/Y%u/Type"%(i+1,i+1),"%u/%u mm"%(round(x/10000.0,2),round(y/10000.0,2))+NodeType,offset+4+i*8,8,"txt",offset+4+pointnum*8+i,1)
	return pointnum

def loda_coords5 (hd,data,offset,l_type):
	for i in range (4):
		x = struct.unpack('<l', data[offset+i*8:offset+4+i*8])[0]
		y = struct.unpack('<l', data[offset+4+i*8:offset+8+i*8])[0]
		add_iter (hd,"[001e] X%u/Y%u"%(i+1,i+1),"%u/%u mm"%(round(x/10000.0,2),round(y/10000.0,2)),offset+i*8,8,"txt")
	offset += 32
	add_iter (hd,"[001e] var1?",struct.unpack("<H",data[offset:offset+2])[0],offset,2,"<H")
	add_iter (hd,"[001e] BPP?",struct.unpack("<H",data[offset+2:offset+4])[0],offset+2,2,"<H")
	add_iter (hd,"[001e] Img Width (px)",struct.unpack("<I",data[offset+4:offset+8])[0],offset+4,4,"<I")
	add_iter (hd,"[001e] Img Height (px)",struct.unpack("<I",data[offset+8:offset+12])[0],offset+8,4,"<I")
	offset += 16
	add_iter (hd,"[001e] Image ID",struct.unpack("<I",data[offset:offset+4])[0],offset,4,"<I")
	offset += 24
	loda_coords3 (hd,data,offset,l_type)


def loda_coords_poly (hd,data,offset,l_type):
	pn = loda_coords3 (hd,data,offset,l_type)
	x = struct.unpack('<l', data[offset+4+pn*9:offset+4+pn*9+4])[0]
	y = struct.unpack('<l', data[offset+4+pn*9+4:offset+4+pn*9+8])[0]
	add_iter (hd,"[001e] var1/var2 ?","%u/%u mm"%(round(x/10000.0,2),round(y/10000.0,2)),offset+4+pn*9,8,"txt")


def loda_coords_0x25(hd,data,offset,l_type):
	numpts = 3+struct.unpack("<H",data[offset+4:offset+6])[0]
	off = offset +8
	for i in range (numpts):
		x = struct.unpack('<l', data[off+i*8:off+4+i*8])[0]
		y = struct.unpack('<l', data[off+4+i*8:off+8+i*8])[0]
		Type = ord(data[off+numpts*8+i])
		NodeType = ''
		# FIXME! Lazy to learn dictionary right now, will fix later
		if Type&2 == 2:
			NodeType = '    Char. start'
		if Type&4 == 4:
			NodeType = NodeType+'  Can modify'
		if Type&8 == 8:
			NodeType = NodeType+'  Closed path'
		if Type&0x10 == 0 and Type&0x20 == 0:
			NodeType = NodeType+'  Discontinued'
		if Type&0x10 == 0x10:
			NodeType = NodeType+'  Smooth'
		if Type&0x20 == 0x20:
			NodeType = NodeType+'  Symmetric'
		if Type&0x40 == 0 and Type&0x80 == 0:
			NodeType = NodeType+'  START'
		if Type&0x40 == 0x40 and Type&0x80 == 0:
			NodeType = NodeType+'  Line'
		if Type&0x40 == 0 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Curve'
		if Type&0x40 == 0x40 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Arc'
		add_iter (hd,"[001e] X%u/Y%u/Type"%(i+1,i+1),"%u/%u mm"%(round(x/10000.0,2),round(y/10000.0,2))+NodeType,off+i*8,8,"txt",off+numpts*8+i,1)
 

def loda_coords (hd,data,offset,l_type):
	if l_type < 5 and l_type != 3:
		loda_coords124 (hd,data,offset,l_type)
	elif l_type == 3:
		loda_coords3 (hd,data,offset,l_type)
	elif l_type == 0x14:
		loda_coords_poly(hd,data,offset,l_type)
	elif l_type == 0x25:
		loda_coords_0x25(hd,data,offset,l_type)
	elif l_type == 5:
		loda_coords5 (hd,data,offset,l_type)
# insert calls to specific coords parsing here
	else:
		add_iter (hd,"[%04x]"%(argtype),"???",offset,struct.unpack('<L',data[s_args+i*4:s_args+i*4+4])[0]-offset,"txt")



def loda_palt (hd,data,offset,l_type):
	clr_model(hd,data,offset)

loda_types = {0:"Layer",1:"Rectangle",2:"Ellipse",3:"Line/Curve",4:"Text",5:"Bitmap",0xb:"Grid",0xc:"Guides",0x11:"Desktop",0x14:"Polygon",0x25:"Path ??"}

# loda_container 1st 4 bytes -- matches with SPND of the group

loda_type_func = {0xa:loda_outl,0x14:loda_fild,0x1e:loda_coords,
									0x28:loda_rot_center,0x64:loda_trfd,
									0xc8:loda_stlt,0x2af8:loda_polygon,0x3e8:loda_name,
									0x2efe:loda_rot,0x7d0:loda_palt #, 0x1f40:loda_lens, 0x1f45:loda_contnr
									}

def loda (hd,size,data):
	n_args = struct.unpack('<i', data[4:8])[0]
	s_args = struct.unpack('<i', data[8:0xc])[0]
	s_types = struct.unpack('<i', data[0xc:0x10])[0]
	l_type = struct.unpack('<i', data[0x10:0x14])[0]
	add_iter (hd, "# of args", n_args,4,4,"<i")
	add_iter (hd, "Start of args offsets", "%02x"%s_args,8,4,"<i")
	add_iter (hd, "Start of arg types", "%02x"%s_types,0xc,4,"<i")
	t_txt = "%02x"%l_type
	if loda_types.has_key(l_type):
		t_txt += " " + loda_types[l_type]
	add_iter (hd, "Type", t_txt,0x10,2,"txt")

	a_txt = ""
	t_txt = ""
	for i in range(n_args,0,-1):
		a_txt += " %04x"%struct.unpack('<L',data[s_args+i*4-4:s_args+i*4])[0]
		t_txt += " %04x"%struct.unpack('<L',data[s_types+(n_args-i)*4:s_types+(n_args-i)*4+4])[0]
	add_iter (hd, "Args offsets",a_txt,s_args,n_args*4,"txt")
	add_iter (hd, "Args types",t_txt,s_types,n_args*4,"txt")

	if loda_types.has_key(l_type):
		for i in range(n_args, 0, -1):
			[offset] = struct.unpack('<L',data[s_args+i*4-4:s_args+i*4])
			[argtype] = struct.unpack('<L',data[s_types + (n_args-i)*4:s_types + (n_args-i)*4+4])
			if loda_type_func.has_key(argtype):
				loda_type_func[argtype](hd,data,offset,l_type)
			else:
				add_iter (hd,"[%04x]"%(argtype),"???",offset,struct.unpack('<L',data[s_args+i*4:s_args+i*4+4])[0]-offset,"txt")
#				print 'Unknown argtype: %x'%argtype                             

def trfd (hd,size,data):
	start = 32
	if hd.version == 13:
		start = 40
	if hd.version == 5:
		start = 18
	add_iter (hd, "x0", "%u"%(struct.unpack('<d', data[start+16:start+24])[0]/10000),start+16,8,"<d")
	add_iter (hd, "y0", "%u"%(struct.unpack('<d', data[start+40:start+48])[0]/10000),start+40,8,"<d")
	for i in (0,1,3,4):                     
		var = struct.unpack('<d', data[start+i*8:start+8+i*8])[0]
		add_iter (hd, "var%d"%(i+1), "%f"%var,start+i*8,8,"<d")

def disp_expose (da, event,pixbuf):
	ctx = da.window.cairo_create()
	ctx.set_source_pixbuf(pixbuf,0,0)
	ctx.paint()
	ctx.stroke()

def disp (hd,size,data,page):
	# naive version, not always works as needed
	bmp = struct.unpack("<I",data[0x18:0x1c])[0]
	bmpoff = struct.pack("<I",len(data)+10-bmp)
	img = 'BM'+struct.pack("<I",len(data)+8)+'\x00\x00\x00\x00'+bmpoff+data[4:]
	pixbufloader = gtk.gdk.PixbufLoader()
	pixbufloader.write(img)
	pixbufloader.close()
	pixbuf = pixbufloader.get_pixbuf()
	imgw=pixbuf.get_width()
	imgh=pixbuf.get_height()
	if page.win != None:
		page.win.destroy()
	page.win = gtk.Window()
	page.win.set_default_size(imgw, imgh)
	da = gtk.DrawingArea()
	page.win.add(da)
	da.connect('expose_event', disp_expose,pixbuf)
	page.win.show_all()

def txsm (hd,size,data):
	add_iter (hd, "txtj id?", d2hex(data[0x28:0x2c]),0x28,4,"txt")
	for i in range(6):
		var = struct.unpack('<d', data[0x2c+i*8:0x2c+8+i*8])[0]
		add_iter (hd, "var%d"%(i+1), "%d"%(var/10000),0x2c+i*8,8,"<d")
	# skip two dwords (values are 0 and 1)
	off = 0x64
	add_iter (hd, "Stlt ID", d2hex(data[off:off+4]),off,4,"txt")
	# skip 1 byte
	off = 0x69
	num = struct.unpack('<I', data[off:off+4])[0]
	add_iter (hd, "Num of recs (Para?)", num,off,4,"<I")
	off = 0x6d
	for i in range(num):
		id = ord(data[off])
		flag1 = ord(data[off+1])
		flag2 = ord(data[off+2])
		flag3 = ord(data[off+3]) # seems to be 8 all the time
		add_iter (hd, "fl0 fl1 fl2 fl3", "%02x %02x %02x %02x"%(id,flag1,flag2,flag3),off,4,"txt")
		off += 4
		if flag2&1 == 1:
			# looks like lang code
			add_iter (hd, "\tunkn1???", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
		if flag2&2 == 2:
			# assumption
			add_iter (hd, "\tunkn2???", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
		if flag2&4 == 4:
			# assumption
			add_iter (hd, "\tunkn4???", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
		if flag2&8 == 8:
			# assumption
			add_iter (hd, "\tunkn8???", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
		if flag2&0x10 == 0x10:
			# assumption
			add_iter (hd, "\tunkn10?", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
		if flag2&0x20 == 0x20:
			# assumption
			add_iter (hd, "\tunkn20?", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
		if flag2&0x40 == 0x40:
			add_iter (hd, "\tOutl ID?", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
		if flag2&0x80 == 0x80:
			add_iter (hd, "\tFild ID?", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
			
		enc = data[off:off+2]
		add_iter (hd, "\tEnc ?", enc,off,2,"txt")
		off += 4

	num2 = struct.unpack('<I', data[off:off+4])[0]
	add_iter (hd, "Num of 'Char'", num2,off,4,"<I")
	off += 4
	for i in range(num2):
		add_iter (hd, "Char %u"%i, d2hex(data[off:off+8]),off,8,"txt")
		off += 8

	txtlen = struct.unpack('<I', data[off:off+4])[0]
	add_iter (hd, "Text length", txtlen,off,4,"<I")
	off += 4
	add_iter (hd, "Text", "",off,txtlen,"txt")


cdr_ids = {"arrw":arrw,"bbox":bbox,"obbx":obbx,"fild":fild,"ftil":ftil,
	"outl":outl,"trfd":trfd,"loda":loda,"DISP":disp,"bmpf":bmpf,"bmp ":bmp,
	"txsm":txsm}

def cdr_open (buf,page,parent):
	# Path, Name, ID
	page.dictmod = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
	chunk = cdrChunk()
	chunk.load (buf,page,parent)

class cdrChunk:
	fourcc = '????'
	hdroffset = 0
	rawsize = 0
	data = ''
	name= ''
	size= 0
	cmpr = False
	number=0

	def stlt(self,page,parent,data):
		offset = 4
		d1 = struct.unpack("<I",data[offset:offset+4])[0]
		add_pgiter(page,"unkn1 [%d]"%d1,"cdr","stlt_d1",data[offset:offset+4],parent)
		offset += 4

		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set0 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"%s | %s | %s"%(d2hex(data[offset:offset+4]),d2hex(data[offset+4:offset+8]),d2hex(data[offset+8:offset+12])),"cdr","stlt_s0",data[offset:offset+12],s_iter)
			offset += 12

		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set1 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"%s | %s | %s"%(d2hex(data[offset:offset+4]),d2hex(data[offset+4:offset+8]),d2hex(data[offset+8:offset+12])),"cdr","stlt_s1",data[offset:offset+12],s_iter)
			offset += 12

		size = 60
		if page.version < 10:
			size = 44
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set2 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s2",data[offset:offset+size],s_iter)
			offset += size

		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set3 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s3",data[offset:offset+12],s_iter)
			offset += 12

		size = 52
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set4 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s4",data[offset:offset+size],s_iter)
			offset += size

		size = 152
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set5 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s5",data[offset:offset+size],s_iter)
			offset += size

		size = 784
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set6 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s6",data[offset:offset+size],s_iter)
			offset += size

		size = 80
		if page.version < 10:  # VERIFY in what version it was changed
			size = 72
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set7 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			# FIXME! seems to have another place to check
			flag = struct.unpack("<I",data[offset+8:offset+12])[0]
			if flag:
				inc = 8
			else:
				inc = 0
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s7",data[offset:offset+size+inc],s_iter)
			offset += size + inc

		size = 28
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set8 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s (pID %s)"%(d2hex(data[offset:offset+4]),d2hex(data[offset+4:offset+8])),"cdr","stlt_s8",data[offset:offset+size],s_iter)
			offset += size
		
		add_pgiter(page,"set9","cdr","stlt_s9",data[offset:offset+72],parent)
		offset += 72

		# size before/after name
		# dword 4:   0      1      2      3
		# ver <10: 48/32  32/8   32/12  32/32
		# ver 10+:   ?    32/8   32/16  32/36

		s_iter = add_pgiter(page,"set10","cdr","","",parent)
		# I only have files with 9 entities here
		for i in range(9):
			id = d2hex(data[offset:offset+4])
			flag = struct.unpack("<I",data[offset+12:offset+16])[0]
			size_bn = 32
			size_an = 36
			if page.version < 10:
				size_an = 32
			if flag == 2:
				size_an -= 20
			elif flag == 1:
				size_an = 8
			elif flag == 0:
				size_bn = 48  # need to check for ver 10+
			namelen = struct.unpack("<I",data[offset+size_bn:offset+4+size_bn])[0]
			if page.version < 10:
				# ended with \0
				name = data[offset+size_bn+4:offset+size_bn+4+namelen-1]
			else:
				name = unicode(data[offset+size_bn+4:offset+4+size_bn+namelen*2],"utf16")
				namelen *= 2
			add_pgiter(page,"ID %s (flag: %02x) [%s]"%(id,flag,name),"cdr","stlt_s10",data[offset:offset+size_bn+4+size_an+namelen],s_iter)
			offset += size_bn+4+size_an+namelen

		if page.version > 9:
			i = 0
			size = 24
			while offset < len(data):
				s_iter = add_pgiter(page,"set11 [%u]"%i,"cdr","","",parent)
				i += 1
				num = struct.unpack("<I",data[offset:offset+4])[0]
				offset += 4
				for j in range(num):
					add_pgiter(page,"ID %s (pID %s)"%(d2hex(data[offset:offset+4]),d2hex(data[offset+4:offset+8])),"cdr","stlt_s8",data[offset:offset+size],s_iter)
					offset += 24

		add_pgiter(page,"Tail","cdr","stlt_tail",data[offset:],parent)


	def load_pack(self,page,parent):
		self.cmpr=True
		decomp = zlib.decompressobj()
		self.uncompresseddata = decomp.decompress(self.data[12:])
		offset = 0
		while offset < len(self.uncompresseddata):
			chunk = cdrChunk()
			chunk.cmpr = True
			chunk.load(self.uncompresseddata, page, f_iter,offset)
			offset += 8 + chunk.rawsize

	def loadcompressed(self,page,parent):
		if self.data[0:4] != 'cmpr':
			raise Exception("can't happen")
		self.cmpr=True
		cmprsize = struct.unpack('<I', self.data[4:8])[0]
		uncmprsize = struct.unpack('<I', self.data[8:12])[0]
		blcks = struct.unpack('<I', self.data[12:16])[0]
		# 16:20 unknown (seen 12, 1096)
		assert(self.data[20:24] == 'CPng')
		assert(struct.unpack('<H', self.data[24:26])[0] == 1)
		assert(struct.unpack('<H', self.data[26:28])[0] == 4)
		if (20 + cmprsize + blcks + 1) & ~1 != self.rawsize:
			raise Exception('mismatched blocksizessize value (20 + %u + %u != %u)' % (cmprsize, blcks, self.rawsize))
		decomp = zlib.decompressobj()
		self.uncmprdata = decomp.decompress(self.data[28:])
		if len(decomp.unconsumed_tail):
			raise Exception('unconsumed tail in compressed data (%u bytes)' % len(decomp.unconsumed_tail))
		if len(decomp.unused_data) != blcks:
			raise Exception('mismatch in unused data after compressed data (%u != %u)' % (len(decomp.unused_data), bytesatend))
		if len(self.uncmprdata) != uncmprsize:
			raise Exception('mismatched compressed data size: expected %u got %u' % (uncmprsize, len(self.uncmprdata)))
		blcksdata = zlib.decompress(self.data[28+cmprsize:])
		blocksizes = []
		for i in range(0, len(blcksdata), 4):
			blocksizes.append(struct.unpack('<I', blcksdata[i:i+4])[0])
		offset = 0
		while offset < len(self.uncmprdata):
			chunk = cdrChunk()
			chunk.cmpr = True
			chunk.load(self.uncmprdata, page,parent,offset, blocksizes)
			offset += 8 + chunk.rawsize

	def load(self, buf, page, parent, offset=0, blocksizes=()):
		self.hdroffset = offset
		self.fourcc = buf[offset:offset+4]
		self.rawsize = struct.unpack('<I', buf[offset+4:offset+8])[0]
		id = self.rawsize
		if len(blocksizes):
			self.rawsize = blocksizes[self.rawsize]
		self.data = buf[offset+8:offset+8+self.rawsize]
		if self.rawsize & 1:
			self.rawsize += 1

		self.name = self.chunk_name()
		f_iter = add_pgiter(page,self.name+" %02x"%id,"cdr",self.name,self.data,parent)
		if self.name == "outl" or self.name == "fild" or self.name == "arrw" or self.name == "bmpf":
			d_iter = page.dictmod.append(None,None)
			page.dictmod.set_value(d_iter,0,page.model.get_path(f_iter))
			page.dictmod.set_value(d_iter,2,d2hex(self.data[0:4]))
			page.dictmod.set_value(d_iter,1,self.name)

		if self.fourcc == 'vrsn':	
			page.version = struct.unpack("<h",self.data)[0]/100
		if self.fourcc == 'pack':	
			self.load_pack(page,f_iter)
		if self.fourcc == 'RIFF' or self.fourcc == 'LIST':
			self.listtype = buf[offset+8:offset+12]
			name = self.chunk_name()
			if self.cmpr == True:
				name += " %02x"%id
			page.model.set_value(f_iter,0,name)
			page.model.set_value(f_iter,1,("cdr",self.name))

			parent = f_iter
			if self.listtype == 'stlt':
				self.name = '<stlt>'
				#pass     # dunno what's up with these, but they're not lists
				self.stlt(page,parent,self.data)
			elif self.listtype == 'cmpr':
				self.loadcompressed(page,parent)
			else:
				offset += 12
				while offset < self.hdroffset + 8 + self.rawsize:
					chunk = cdrChunk()
					chunk.load(buf,page,parent,offset, blocksizes)
					offset += 8 + chunk.rawsize

	def chunk_name(self):
		if self.fourcc == 'RIFF':
			return self.fourcc
		if hasattr(self, 'listtype'):
			return self.listtype
		return self.fourcc
