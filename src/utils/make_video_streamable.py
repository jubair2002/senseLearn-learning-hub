"""
Utility script to make MP4 videos streamable (fast start).
This moves the metadata (moov atom) to the beginning of the file,
allowing browsers to seek to any position without downloading the entire video.

Requirements:
    ffmpeg must be installed on the system

Usage:
    python -m src.utils.make_video_streamable input_video.mp4 output_video.mp4
"""

import sys
import os
import subprocess

def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def make_streamable(input_path, output_path=None, logger=None):
    """
    Convert video to streamable format (fast start).
    
    Args:
        input_path: Path to input video file
        output_path: Path to output video file (optional, defaults to replacing input file)
        logger: Optional logger instance for logging (if None, uses print)
    
    Returns:
        tuple: (success: bool, output_path: str or None, error_message: str or None)
    """
    if not os.path.exists(input_path):
        error_msg = f"File not found: {input_path}"
        if logger:
            logger.error(error_msg)
        else:
            print(f"Error: {error_msg}")
        return False, None, error_msg
    
    if not check_ffmpeg():
        error_msg = "ffmpeg is not installed. Video will be uploaded as-is (may not be streamable)."
        if logger:
            logger.warning(error_msg)
        else:
            print(f"Warning: {error_msg}")
        return False, None, error_msg
    
    # If no output path specified, replace the input file
    if output_path is None:
        output_path = input_path
    
    log_msg = f"Converting video to streamable format: {os.path.basename(input_path)}"
    if logger:
        logger.info(log_msg)
    else:
        print(log_msg)
    
    try:
        # Use ffmpeg to remux video with faststart flag
        # This moves the moov atom to the beginning without re-encoding
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c', 'copy',  # Copy streams without re-encoding (fast)
            '-movflags', '+faststart',  # Move metadata to beginning
            '-y',  # Overwrite output file
            output_path
        ]
        
        # Run with timeout (30 seconds per MB, max 5 minutes)
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
        timeout = min(int(file_size_mb * 30), 300)  # Max 5 minutes
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        
        if result.returncode == 0:
            success_msg = f"Video converted to streamable format successfully"
            if logger:
                logger.info(success_msg)
            else:
                print(f"✓ {success_msg}")
            return True, output_path, None
        else:
            error_msg = f"FFmpeg conversion failed: {result.stderr[:200]}"
            if logger:
                logger.error(error_msg)
            else:
                print(f"Error: {error_msg}")
            return False, None, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = "Video conversion timed out"
        if logger:
            logger.error(error_msg)
        else:
            print(f"Error: {error_msg}")
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Conversion error: {str(e)}"
        if logger:
            logger.exception(error_msg)
        else:
            print(f"Error: {error_msg}")
        return False, None, error_msg

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.make_video_streamable <input_video> [output_video]")
        print("\nExample:")
        print("  python -m src.utils.make_video_streamable video.mp4")
        print("  python -m src.utils.make_video_streamable video.mp4 video_streamable.mp4")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success, output_path, error = make_streamable(input_file, output_file)
    if success:
        print(f"✓ Success! Video is now streamable: {output_path}")
        print(f"  Original size: {os.path.getsize(input_file) / (1024*1024):.2f} MB")
        if output_path != input_file:
            print(f"  New size: {os.path.getsize(output_path) / (1024*1024):.2f} MB")
    else:
        print(f"Error: {error}")
    sys.exit(0 if success else 1)

