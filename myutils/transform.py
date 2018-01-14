import numpy as np
import cv2
from tqdm import tqdm
from sklearn.preprocessing import normalize

def draw_BB(image, l, t, r, b):
    out = np.copy(image)
    lt = (int(l * image.shape[1]), int(t * image.shape[0]))
    rb = (int(r * image.shape[1]), int(b * image.shape[0]))
    cv2.rectangle(out, lt, rb, (0, 255, 0), 2)
    return out

def get_BB(image):
    a = np.where(image != 0)
    return np.min(a[1])/640, np.min(a[0])/480, \
           np.max(a[1])/640, np.max(a[0])/480

def RT2to4x4(R, t):
    pose = np.zeros((4, 4))
    np.copyto(pose[0:3, 0:3], R)
    np.copyto(pose[0:3, 3:4], t)
    return pose

def lookAt(src, dst):
    src = np.array(src)
    dst = np.array(dst)
    forward = normalize([dst - src]).flatten()
    right = normalize([np.cross(forward, [0, 0, 1])]).flatten()
    down = normalize([np.cross(forward, right)]).flatten()

    camToWorld = np.zeros((4, 4))

    camToWorld[0][0] = right[0]
    camToWorld[1][0] = right[1]
    camToWorld[2][0] = right[2]
    camToWorld[0][1] = down[0]
    camToWorld[1][1] = down[1]
    camToWorld[2][1] = down[2]
    camToWorld[0][2] = forward[0]
    camToWorld[1][2] = forward[1]
    camToWorld[2][2] = forward[2]

    camToWorld[0][3] = src[0]
    camToWorld[1][3] = src[1]
    camToWorld[2][3] = src[2]
    camToWorld[3][3] = 1.

    worldToCam = np.linalg.inv(camToWorld)

    return worldToCam[:3, :3], worldToCam[:3, 3:4]

rx, ry, rz = 0., 0., 0.
def getView(radius):
    R = np.matmul(angle2Rot(0, np.pi, 0), angle2Rot(0, -np.pi / 2, np.pi / 2))
    X = [[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]]
    Y = [[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]]
    Z = [[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]]
    R = np.matmul(X, np.matmul(Y, R))
    t = np.array([0, 0, radius])
    return {'R': R, 't': t}

def getRandomView(radius):
    theta = np.random.uniform(-np.pi, np.pi)
    u = np.random.uniform(-1, 1)
    v = np.random.uniform(-1, 1)
    x = np.sqrt(1 - np.square(u)) * np.cos(v * np.pi)
    y = np.sqrt(1 - np.square(u)) * np.sin(v * np.pi)
    z = u
    rvec = np.array([x, y, z])
    rvec = rvec / np.linalg.norm(rvec) * theta
    R = cv2.Rodrigues(rvec)[0]
    t = np.array([0, 0, radius])
    if R[2][2] > 0:
        return getRandomView(radius)
    else:
        return {'R': R, 't': t, 'rvec': rvec.tolist()}

def getRandomView1(radius, inplane_range=np.pi/2):
    # Uniformly sampled on a sphere
    u = np.random.rand()
    v = np.random.rand()
    w = np.random.uniform(-inplane_range * np.sqrt(1 - u),
                           inplane_range * np.sqrt(1 - u))
    x = np.sqrt(1 - np.square(u)) * np.cos(v * 2 * np.pi) * radius
    y = np.sqrt(1 - np.square(u)) * np.sin(v * 2 * np.pi) * radius
    z = u * radius
    R, t = lookAt([x, y, z], [0, 0, 0])
    R = np.matmul(np.array([[np.cos(w), -np.sin(w), 0],
                            [np.sin(w), np.cos(w), 0],
                            [0, 0, 1]]), R)
    a = v * 2 * np.pi
    b = np.arctan(z / np.sqrt(x ** 2 + y ** 2))
    c = w
    return {'R': R, 't': t, 'a': a, 'b': b, 'c': c}

def getRandomView2(radius, inplane_range=np.pi/2):
    a = np.random.rand() * 2 * np.pi
    b = np.random.rand() * np.pi / 2
    c = np.random.uniform(-inplane_range * (1 - b / (np.pi / 2)),
                           inplane_range * (1 - b / (np.pi / 2)))
    x = np.cos(b) * np.cos(a) * radius
    y = np.cos(b) * np.sin(a) * radius
    z = np.sin(b) * radius
    R, t = lookAt([x, y, z], [0, 0, 0])
    R = np.matmul(np.array([[np.cos(c), -np.sin(c), 0],
                            [np.sin(c), np.cos(c), 0],
                            [0, 0, 1]]), R)
    return {'R': R, 't': t, 'a': a, 'b': b, 'c': c}

def getViews(view_count, view_radius):
    views = []
    global rx, ry, rz
    rx, ry, rz = np.pi * 0.1, np.pi * 0.7, 0.
    for i in tqdm(range(view_count), 'Generating views: '):
        views.append(getView(view_radius))
    return views

def getRandomViews(view_count, view_radius):
    views = []
    for i in tqdm(range(view_count), 'Generating random views: '):
        views.append(getRandomView(view_radius))
    return views

def abc2Rt(a, b, c, radius):
    x = np.cos(b) * np.cos(a) * radius
    y = np.cos(b) * np.sin(a) * radius
    z = np.sin(b) * radius
    R, t = lookAt([x, y, z], [0, 0, 0])
    R = np.matmul(np.array([[np.cos(c), -np.sin(c), 0],
                            [np.sin(c), np.cos(c), 0],
                            [0, 0, 1]]), R)
    return R, t

def uv2ab(u, v):
    x = np.sqrt(1 - np.square(u)) * np.cos(v * 2 * np.pi)
    y = np.sqrt(1 - np.square(u)) * np.sin(v * 2 * np.pi)
    z = u
    a = v
    b = np.arctan(z / np.sqrt(x**2 + y**2))
    return a, b

def ab2uv(a, b):
    u = np.sin(b)
    v = a
    return u, v

def rot2Angle(R):
    return np.arctan2(R[2][1], R[2][2]), \
           np.arctan2(-R[2][0], np.sqrt(R[2][1]**2 + R[2][2]**2)), \
           np.arctan2(R[1][0], R[0][0])

def angle2Rot(rx, ry, rz):
    X = [[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]]
    Y = [[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]]
    Z = [[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]]
    return np.matmul(Z, np.matmul(Y, X))



