/** Turns camera captures into small base64 JPEGs, so uploads stay light on 2G/3G connections. */

const PHOTO_MAX_SIDE = 1024
const FRAME_MAX_SIDE = 640
const JPEG_QUALITY = 0.75

function canvasToBase64(source: CanvasImageSource, width: number, height: number, maxSide: number) {
  const scale = Math.min(1, maxSide / Math.max(width, height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(width * scale)
  canvas.height = Math.round(height * scale)
  canvas.getContext('2d')!.drawImage(source, 0, 0, canvas.width, canvas.height)
  return canvas.toDataURL('image/jpeg', JPEG_QUALITY).split(',')[1]
}

export async function photoToBase64(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file)
  try {
    return canvasToBase64(bitmap, bitmap.width, bitmap.height, PHOTO_MAX_SIDE)
  } finally {
    bitmap.close()
  }
}

/** Evenly spaced still frames from a short video; the AI reads them in order. */
export async function videoToFrames(file: File, frameCount = 6): Promise<string[]> {
  const video = document.createElement('video')
  video.muted = true
  video.src = URL.createObjectURL(file)
  try {
    await new Promise<void>((resolve, reject) => {
      video.onloadeddata = () => resolve()
      video.onerror = () => reject(new Error('Video could not be read'))
    })
    const frames: string[] = []
    for (let index = 0; index < frameCount; index += 1) {
      video.currentTime = (video.duration * (index + 0.5)) / frameCount
      await new Promise((resolve) => (video.onseeked = resolve))
      frames.push(canvasToBase64(video, video.videoWidth, video.videoHeight, FRAME_MAX_SIDE))
    }
    return frames
  } finally {
    URL.revokeObjectURL(video.src)
  }
}

export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result).split(',')[1])
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(blob)
  })
}
