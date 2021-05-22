
d1 = {'a':[1],'b':[2],'c':3}
d2 = {'a': 6, 'b': 7,'d':[8]}
d3 = {'a': 11, 'd': [12],'e':[8]}
d5 = {'f':3,'d':[34], 'g':5}
d6= {'h':[30],'b':[4],"a":[5],'c':[31,67],'d':74,"g":55,"g":65}
d7= {'a':52}
d4={}
values=[]
for i in [d1,d2,d3,d5,d6,d7]:
    for j,k in i.items():
        if j not in d4:
            if isinstance(j,str):
                value=[]
                d4.update({j: value})
            if isinstance(k,list):
                value.append(k[0])
            else:
                value.append(k)
        else:
            v1=d4[j]
            if isinstance(k, list):
                v1.extend(k)
            else:
                if isinstance(v1,list):
                    v1.append(k)

print(d4)









#
# aa = ["a", 1, 2, 3, 4, 5, "b", 6, 7, 8, 9, "c", 10, 11, 12, 13, "d", 14, 15, 16, 17]
#
# dic={}
# values=[]
# for i in aa:
#     if isinstance(i,str):
#       values=[]
#       dic[i]=values
#     else:
#       values.append(i)
# print(dic)
#
