from __future__ import print_function
"""

#Load 10K vectors into memory and 500K vectors total
#both of the following work
wv=lwvlib.load("somefile.bin",10000,500000)
wv=lwvlib.WV.load("somefile.bin",10000,500000)

wv.max_rank_mem
wv.max_rank

#Normalized vector for "koira", gives None if word unknown
wv.w_to_normv(u"koira")

#Index of "koira"
wv[u"koira"] #throws exception if koira not present
wv.get(u"koira") #returns None if koira not present
wv.w_to_dim(u"koira")

#Do I have "koira"?
u"koira" in wv
wv.get(u"koira") is not None
u"koira" in wv.w_to_dim

#7 nearest words as a list [(similarity,word),(similarity,word)]
wv.nearest(u"koira",7)

#The raw vectors in numpy array
wv.vectors

#List of words
wv.words


#Lengths of all vectors in the array (ie wv.max_rank_mem many of them)
wv.norm_constants

# Module-level utility functions

load()
bin2txt()
txt2bin()


"""

import traceback
import numpy
import mmap
import os
#import StringIO
import struct
import sys

#so we can write lwvlib.load(...)
def load(*args,**kwargs):
    return WV.load(*args,**kwargs)


class WV(object):

    @staticmethod
    def read_word(inp):
        """
        Reads a single word from the input file
        """
        chars=[]
        while True:
            c = inp.read(1)
            if c == b' ':
                break
            if not c:
                raise ValueError("preliminary end of file")
            chars.append(c)
        wrd=b''.join(chars).strip()
        try:
            return wrd.decode("utf-8")
        except UnicodeDecodeError:
            #Not a utf-8, shoots, what now?
            #maybe I should warn here TODO
            return wrd.decode("utf-8","replace")

    @classmethod
    def load(cls,file_name,*args,format=None,**kwargs):
        #which format?
        if format==None:
            #guess on suffix
            if isinstance(file_name,str):
                ext=os.path.splitext(file_name)[1]
                if ext in (".txt",".vector",".vectors"):
                    format="txt"
                elif ext in (".bin",):
                    format="bin"
        if format=="txt":
            return cls.load_txt(file_name,*args,**kwargs)
        elif format=="bin" or format is None:
            return cls.load_bin(file_name,*args,**kwargs)

    @classmethod
    def load_txt(cls,file_name,max_rank_mem=None,max_rank=None,float_type=numpy.float32):
        """
        Loads a w2v vectors file.
        `inp` an open file or a file name
        `max_rank_mem` read up to this many vectors into an internal matrix, the rest is memory-mapped
        `max_rank` read up to this many vectors, memory-mapping whatever above max_rank_mem
        `float_type` the type of the vector matrix
        """
        ### Manually decoding utf-8 because sometimes we have unicode errors
        f=open(file_name,"rb")
        try:
            l=f.readline().decode("utf-8").strip()
            wcount,vsize=l.split()
            wcount,vsize=int(wcount),int(vsize)
        except ValueError:
            raise ValueError("Size line in the file is malformed: '%s'. Maybe this is not a w2v binary file?"%l)

        if max_rank is None or max_rank>wcount:
            max_rank=wcount

        if max_rank_mem is None or max_rank_mem>max_rank:
            max_rank_mem=max_rank

        if max_rank_mem!=max_rank:
            raise ValueError("max-rank-mem and max-rank must equal when reading the text format")

        words=[]
        data=numpy.zeros((max_rank_mem,vsize),float_type)
        for idx in range(max_rank_mem):
            line=f.readline().rstrip()
            word,weights=line.split(b" ",1)
            try:
                word=word.decode("utf-8")
            except UnicodeDecodeError:
                #A broken word
                broken=word
                for goodchar_idx in range(len(broken)-1,-1,-1):
                    try:
                        word=broken[:goodchar_idx].decode("utf-8")
                    except UnicodeDecodeError:
                        continue
                    #Success!
                    #print("Fixing UTF8 error:",file=sys.stderr,flush=True)
                    #sys.stderr.buffer.write(broken)
                    #print("  ->",word,file=sys.stderr,flush=True)
                    break
                else:
                    #Wow, couldn't fix
                    word="utf8err{}".format(idx) #makes them unique
            weights=weights.decode("utf-8")
            words.append(word)
            vec=numpy.fromstring(weights,numpy.float32,vsize,sep=" ")
            data[idx,:]=vec
        return cls(words,data,None,None)


    @classmethod
    def load_bin(cls,file_name,max_rank_mem=None,max_rank=None,float_type=numpy.float32):
        """
        Loads a w2v bin file.
        `inp` an open file or a file name
        `max_rank_mem` read up to this many vectors into an internal matrix, the rest is memory-mapped
        `max_rank` read up to this many vectors, memory-mapping whatever above max_rank_mem
        `float_type` the type of the vector matrix
        """
        f=open(file_name,"r+b")
        #Read the size line
        try:
            l=f.readline().strip()
            wcount,vsize=l.split()
            wcount,vsize=int(wcount),int(vsize)
        except ValueError:
            raise ValueError("Size line in the file is malformed: '%s'. Maybe this is not a w2v binary file?"%l)

        if max_rank is None or max_rank>wcount:
            max_rank=wcount

        if max_rank_mem is None or max_rank_mem>max_rank:
            max_rank_mem=max_rank

        #offsets: byte offsets at which the vectors start
        offsets=[]
        #words: the words themselves
        words=[]
        #data: the vector matrix for the first max_rank vectors
        data=numpy.zeros((max_rank_mem,vsize),float_type)
        #Now read one word at a time, fill into the matrix
        for idx in range(max_rank_mem):
            words.append(cls.read_word(f))
            offsets.append(f.tell())
            data[idx,:]=numpy.fromfile(f,numpy.float32,vsize)
        #Keep reading, but only remember the offsets
        for idx in range(max_rank_mem,max_rank):
            words.append(cls.read_word(f))
            offsets.append(f.tell())
            f.seek(vsize*4,os.SEEK_CUR) #seek over the vector (4 is the size of float32)
        fm=mmap.mmap(f.fileno(),0)
        return cls(words,data,fm,offsets)

    def __init__(self,words,vector_matrix,mm_file,offsets):
        """
        `words`: list of words
        `vector_matrix`: numpy matrix
        `mm_file`: memory-mapped .bin file with the vectors
        `offsets`: for every word, the offset at which its vector starts
        """
        self.vectors=vector_matrix #Numpy matrix
        self.words=words #The words to go with them
        self.w_to_dim=dict((w,i) for i,w in enumerate(self.words))
        self.mm_file=mm_file
        self.offsets=offsets
        self.max_rank_mem,self.vsize=self.vectors.shape
        #normalization constants for every row
        self.norm_constants=numpy.linalg.norm(x=self.vectors,ord=None,axis=1)#.reshape(self.max_rank,1) #Column vector of norms

    def __contains__(self,wrd):
        return wrd in self.w_to_dim

    def get(self,wrd,default=None):
        """Returns the vocabulary index of wrd or default"""
        return self.w_to_dim.get(wrd,default)

    def __getitem__(self,wrd):
        return self.w_to_dim[wrd]

    def w_to_normv(self,wrd):
        #Return a normalized vector for wrd if you can, None if you cannot
        wrd_dim=self.w_to_dim.get(wrd)
        if wrd_dim is None:
            return None #We know nothing of this word, sorry
        if wrd_dim<self.max_rank_mem: #We have the vector loaded in memory
            return self.vectors[wrd_dim]/self.norm_constants[wrd_dim]
        else: #We don't have the vector loaded in memory, grab it from the file
            vec=numpy.fromstring(self.mm_file[self.offsets[wrd_dim]:self.offsets[wrd_dim]+self.vsize*4],numpy.float32,self.vsize).astype(self.vectors.dtype)
            vec/=numpy.linalg.norm(x=vec,ord=None)
            return vec

    def nearest_to_normv(self,wrd_vec_norm,N=10):
        sims=self.vectors.dot(wrd_vec_norm)/self.norm_constants #cosine similarity to all other vecs
        #http://stackoverflow.com/questions/6910641/how-to-get-indices-of-n-maximum-values-in-a-numpy-array
        nearest_n=sorted(((sims[idx],self.words[idx]) for idx in numpy.argpartition(sims,-N-1)[-N-1:]), reverse=True) #this should be n+1 long
        return nearest_n

    def nearest(self,wrd,N=10):
        wrd_vec_norm=self.w_to_normv(wrd)
        if wrd_vec_norm is None:
            return
        nearest_n=self.nearest_to_normv(wrd_vec_norm,N)
        if nearest_n[0][1]==wrd:
            return nearest_n[1:]
        else:
            return nearest_n[:-1]


    def similarity(self,w1,w2):
        """
        Return similarity of two words
        """
        w1_norm=self.w_to_normv(w1)
        w2_norm=self.w_to_normv(w2)
        if w1_norm is None or w2_norm is None:
            return
        return numpy.dot(w1_norm,w2_norm)

    def similarity_sentences(self, sentences):
        embeddings = []
        for sentence in sentences:
            s_emb = []
            for word in sentence:
                word_norm = self.w_to_normv(word)
                if not word_norm is None:
                    s_emb.append(word_norm)
            if len(s_emb) == 0:
                # array is zero
                embeddings.append(numpy.zeros(self.vsize))
            else:
                embeddings.append(numpy.mean(numpy.array(s_emb), axis=0))
        embeddings = numpy.array(embeddings)
        return numpy.inner(embeddings, embeddings)

    def analogy(self,src1,target1,src2,N=10):
        """
        src1 is to target1 as src2 is to ____
        """
        src1nv=self.w_to_normv(src1)
        target1nv=self.w_to_normv(target1)
        src2nv=self.w_to_normv(src2)
        if None in (src1nv,target1nv,src2nv):
            return None
        target2=src2nv+target1nv-src1nv
        target2/=numpy.linalg.norm(target2,ord=None)
        sims=self.vectors.dot(target2)/self.norm_constants #cosine similarity to all other vecs
        return sorted(((sims[idx],self.words[idx]) for idx in numpy.argpartition(sims,-N-1)[-N-1:]), reverse=True)[1:]

    def save_bin(self,f_out):
        #Careful, only saves what's loaded in mem
        if isinstance(f_out,str):
            out=open(f_out,"wb")
        else:
            out=f_out
        out.write("{} {}\n".format(*self.vectors.shape).encode("utf-8"))
        for idx in range(self.vectors.shape[0]):
            out.write(self.words[idx].encode("utf-8"))
            out.write(" ".encode("utf-8"))
            self.vectors[idx].tofile(out,sep="")
            out.write("\n".encode("utf-8"))
        out.close()

    def save_txt(self,f_out):
        #Careful, only saves what's loaded in mem
        if isinstance(f_out,str):
            out=open(f_out,"wt")
        else:
            out=f_out
        out.write("{} {}\n".format(*self.vectors.shape))
        for idx in range(self.vectors.shape[0]):
            out.write(self.words[idx])
            out.write(" ")
            self.vectors[idx].tofile(out,sep=" ",format="%.6f")
            out.write("\n")
        out.close()



def txt2bin(f_in,f_out,max=0):
    """
    convert UDPipe's (and Mikolov's?) txt format to bin
    `f_in` string or open file (will be closed)
    `f_out` string or open file (will be closed)
    """
    if isinstance(f_in,str):
        inp=open(f_in,"rt")
    else:
        inp=f_in
    if isinstance(f_out,str):
        out=open(f_out,"wb")
    else:
        out=f_out
    sizes=inp.readline()
    rows, dims=sizes.strip().split()
    rows, dims=int(rows), int(dims)
    if max>0:
        rows=max(rows,max)
    out.write("{} {}\n".format(rows,dims).encode("utf-8"))
    counter=0

    for line in inp:
        line=line.rstrip()
        line=line.lstrip(" ")
        word,rest=line.split(" ",1)
        out.write(word.encode("utf-8"))
        out.write(" ".encode("utf-8"))
        out.write(struct.pack("{}f".format(dims),*(float(w) for w in rest.split())))
        counter+=1
        if counter==rows:
            break


    inp.close()
    out.close()

def bin2txt(f_in,f_out,max_num=0):
    """
    convert bin to UDPipe's (and Mikolov's?) txt format
    `f_in` string with .bin file name
    `f_out` string or open file (will be closed)
    """
    if max_num>0:
        m=load(f_in,max_num,max_num)
    else:
        m=load(f_in)

    if isinstance(f_out,str):
        out=open(f_out,"w")
    else:
        out=f_out

    print("{} {}".format(*m.vectors.shape),file=out)
    for w,row in zip(m.words,m.vectors):
        print(w," ".join(("{:6f}".format(x) for x in row)),file=out)
    out.close()
