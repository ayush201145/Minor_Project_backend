import React, { useState } from 'react';

const VideoUploader = ({ videoFiles, setVideoFiles, onUploadSuccess }) => {
    const [isUploading, setIsUploading] = useState(false);

    const handleFile = (index, e) => {
        const newFiles = [...videoFiles];
        newFiles[index] = e.target.files[0];
        setVideoFiles(newFiles);
    };

    const submit = async () => {
        if (videoFiles.includes(null)) return alert("Upload all 4 videos.");
        setIsUploading(true);
        const formData = new FormData();
        videoFiles.forEach((file, i) => formData.append(`lane${i+1}`, file));

        try {
            const res = await fetch("http://localhost:8000/upload", { method: "POST", body: formData });
            if (res.ok) onUploadSuccess();
        } catch (err) {
            console.error(err);
            alert("Upload failed. Make sure your Express backend is running!");
        }
        setIsUploading(false);
    };

    return (
        <div style={{ background: '#f4f4f4', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
            <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>Configure Intersection Environment</h2>
            
            {/* THIS IS THE FIX: Changed from repeat(4, 1fr) to 1fr 1fr to force a 2x2 grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
                
                {/* Lane 1 */}
                <div style={{ padding: '15px', background: '#fff', border: '1px solid #ccc', borderRadius: '5px' }}>
                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '10px' }}>Lane 1 (North)</label>
                    <input type="file" accept="video/mp4" onChange={(e) => handleFile(0, e)} />
                </div>

                {/* Lane 2 */}
                <div style={{ padding: '15px', background: '#fff', border: '1px solid #ccc', borderRadius: '5px' }}>
                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '10px' }}>Lane 2 (East)</label>
                    <input type="file" accept="video/mp4" onChange={(e) => handleFile(1, e)} />
                </div>

                {/* Lane 3 */}
                <div style={{ padding: '15px', background: '#fff', border: '1px solid #ccc', borderRadius: '5px' }}>
                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '10px' }}>Lane 3 (South)</label>
                    <input type="file" accept="video/mp4" onChange={(e) => handleFile(2, e)} />
                </div>

                {/* Lane 4 */}
                <div style={{ padding: '15px', background: '#fff', border: '1px solid #ccc', borderRadius: '5px' }}>
                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '10px' }}>Lane 4 (West)</label>
                    <input type="file" accept="video/mp4" onChange={(e) => handleFile(3, e)} />
                </div>

            </div>

            <div style={{ textAlign: 'center' }}>
                <button 
                    onClick={submit} 
                    disabled={isUploading} 
                    style={{ 
                        padding: '12px 24px', 
                        background: '#4CAF50', 
                        color: 'white', 
                        border: 'none',
                        borderRadius: '5px',
                        fontSize: '16px',
                        cursor: 'pointer',
                        width: '100%',
                        maxWidth: '300px'
                    }}>
                    {isUploading ? "Uploading..." : "Upload & Start Simulation"}
                </button>
            </div>
        </div>
    );
};

export default VideoUploader;