"""
Quick-and-dirty visualization scripts for a variety of tasks.    
"""

import sequential_e2c as e2c
#import e2c_plane_z as e2c

import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
from data.plane_data2 import PlaneData, get_params

import ipdb as pdb

def show_recons_samples(sess, ckptfile):
  # visualize sample reconstructions
  e2c.saver.restore(sess, ckptfile) # restore variable values
  dataset=PlaneData("data/plane1.npz","data/env1.png")
  dataset.initialize()
  (x_val,u_val,x_next_val)=dataset.sample(e2c.batch_size)
  xr,xp=sess.run([e2c.x_recons, e2c.x_predict],feed_dict={e2c.x:x_val,e2c.u:u_val,e2c.x_next:x_next_val})
  #xr,xp=sess.run([e2c.x_recons0, e2c.x_predict0],feed_dict={e2c.x0:x_val,e2c.u0:u_val,e2c.x1:x_next_val})
  A,B=e2c.A,e2c.B
  def getimgs(x,xnext):
    padsize=1
    padval=.5
    ph=B+2*padsize
    pw=A+2*padsize
    img=np.ones((10*ph,2*pw))*padval
    for i in range(10):
      startr=i*ph+padsize
      img[startr:startr+B,padsize:padsize+A]=x[i,:].reshape((A,B))
    for i in range(10):
      startr=i*ph+padsize
      img[startr:startr+B,pw+padsize:pw+padsize+A]=xnext[i,:].reshape((A,B))
    return img
  fig,arr=plt.subplots(1,2)
  arr[0].matshow(getimgs(x_val,x_next_val),cmap=plt.cm.gray,vmin=0,vmax=1)
  arr[0].set_title('Data')
  arr[1].matshow(getimgs(xr,xp),cmap=plt.cm.gray,vmin=0,vmax=1)
  arr[1].set_title('Reconstruction')
  plt.show()

def show_recons_seq(sess, ckptfile):
  e2c.saver.restore(sess, ckptfile) # restore variable values
  dataset=PlaneData("data/plane1.npz","data/env1.png")
  dataset.initialize()
  T=e2c.T
  print(T)
  (x_vals,u_vals)=dataset.sample_seq(e2c.batch_size,T)
  feed_dict={}
  for t in range(T):
    feed_dict[e2c.xs[t]] = x_vals[t]
  for t in range(T-1):
    feed_dict[e2c.us[t]] = u_vals[t]
  
  fetches=e2c.x_recons + e2c.x_predicts
  results=sess.run(fetches,feed_dict)
  xr=results[:T-1]
  xp=results[T-1:]
  A,B=e2c.A,e2c.B
  def getimgs(x):
    padsize=1
    padval=.5
    ph=B+2*padsize
    pw=A+2*padsize
    img=np.ones((ph,len(x)*pw))*padval
    for t in range(len(x)):
      startc=t*pw+padsize
      img[padsize:padsize+B, startc:startc+A]=x[t][1,:].reshape((A,B))
    return img
  fig,arr=plt.subplots(3,1)
  arr[0].matshow(getimgs(x_vals),cmap=plt.cm.gray,vmin=0,vmax=1)
  arr[0].set_title('X')
  arr[1].matshow(getimgs(xr),cmap=plt.cm.gray,vmin=0,vmax=1)
  arr[1].set_title('Reconstruction')
  arr[2].matshow(getimgs(xp),cmap=plt.cm.gray,vmin=0,vmax=1)
  arr[2].set_title('Prediction')
  plt.show()

def viz_z(sess, ckptfile):
  e2c.saver.restore(sess,ckptfile) # restore variable values
  dataset=PlaneData("data/plane1.npz","data/env1.png")
  Ps,NPs=dataset.getPSpace()
  batch_size=e2c.batch_size
  n0=NPs.shape[0]
  if False:
    Ps=np.vstack((Ps,NPs))
  xy=np.zeros([Ps.shape[0], 2])
  xy[:,0]=Ps[:,1]
  xy[:,1]=20-Ps[:,0] # for the purpose of computing theta, map centered @ origin
  Zs=np.zeros([Ps.shape[0], e2c.z_dim])

  theta=np.arctan(xy[:,1]/xy[:,0])
  for i in range(Ps.shape[0] // batch_size):
    print("batch %d" % i)
    x_val=dataset.getXPs(Ps[i*batch_size:(i+1)*batch_size,:])
    Zs[i*batch_size:(i+1)*batch_size,:]=sess.run(e2c.z, {e2c.x:x_val})
  # last remaining points may not fit precisely into 1 minibatch.
  x_val=dataset.getXPs(Ps[-batch_size:,:])
  Zs[-batch_size:,:]=sess.run(e2c.z, {e2c.x:x_val})

  if False:
    theta[-n0:]=1;

  fig,arr=plt.subplots(1,2)
  arr[0].scatter(Ps[:,1], 40-Ps[:,0], c=(np.pi+theta)/(2*np.pi))
  arr[0].set_title('True State Space')
  arr[1].scatter(Zs[:,0],Zs[:,1], c=(np.pi+theta)/(2*np.pi))
  arr[1].set_title('Latent Space Z')
  #plt.show()
  return fig
 
def viz_z_unfold(sess, cpktprefix):
  d=100 # interval
  for i in range(int(1e5) // d):
    f="%s-%05d" % (cpktprefix,i*d)
    ckptfile=f+".ckpt"
    print(ckptfile)
    fig=viz_z(sess,ckptfile)
    fig.suptitle('%d'%(i*d))
    fig.savefig(f+".png")
    # combine with convert -delay 10 -loop 0 e2c-plane-*.png out.gif
    # then reduce size using gifsicle -O3-colors 256 < out.gif > new.gif
  print('done!')

if __name__=="__main__":
  sess=tf.InteractiveSession()
  #viz_z_unfold(sess, "/ltmp/e2c-plane")
  fig=viz_z(sess,"/ltmp/e2c-plane-199000.ckpt")
  #show_recons_samples(sess,"/ltmp/e2c-plane-186000.ckpt")
  show_recons_seq(sess, "/ltmp/e2c-plane-199000.ckpt")
  plt.show()
  sess.close()