import { useEffect, useRef } from 'react';
import { useAppStore } from '../store/useAppStore';
import { ThreeRobotHead } from '../utils/three-robot';
import { motion } from 'framer-motion';
import { api } from '../api/apiClient';
import { AudioStreamer } from '../utils/audioStreamer';

export function LiveInterview() {
  const { 
    activeSessionId,
    interviewState, 
    visionMetrics, 
    interviewMessages,
    setInterviewState,
    addInterviewMessage,
    updateVisionMetrics
  } = useAppStore();
  
  const threeRef = useRef(null);
  const interviewWsRef = useRef(null);
  const visionWsRef = useRef(null);
  const audioStreamerRef = useRef(null);

  useEffect(() => {
    let robotHead = null;
    if (threeRef.current) {
      robotHead = new ThreeRobotHead('threejs-container-ANIMATION_1');
      robotHead.init();
    }
    return () => {
      if (robotHead) {
        robotHead.destroy();
      }
    };
  }, []);

  useEffect(() => {
    if (!activeSessionId) return;

    // 1. Connect Interview WebSocket
    const iWs = api.connectInterviewSocket(activeSessionId);
    interviewWsRef.current = iWs;

    iWs.onopen = async () => {
      console.log("Interview WS Connected");
      const streamer = new AudioStreamer(iWs);
      audioStreamerRef.current = streamer;
      try {
        await streamer.start();
        setInterviewState('LISTENING');
      } catch (e) {
        console.error("Microphone access denied", e);
        setInterviewState('ERROR');
      }
    };

    iWs.onmessage = (event) => {
      if (typeof event.data === "string") {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === "agent_speech") {
            setInterviewState('SPEAKING');
            addInterviewMessage({ sender: 'agent', content: payload.text });
          } else if (payload.type === "partial_transcript") {
            // Real-time transcript updates can go here if needed
          }
        } catch (e) {
          console.error("Failed to parse JSON payload", e);
        }
      } else if (event.data instanceof Blob) {
        // 3. Play incoming MP3 from AI
        const audioUrl = URL.createObjectURL(event.data);
        const audio = new Audio(audioUrl);
        audio.onended = () => {
          setInterviewState('LISTENING');
        };
        audio.play().catch(e => console.error("Audio playback failed:", e));
      }
    };

    // 2. Connect Vision WebSocket (Mock telemetry loop)
    const vWs = api.connectVisionSocket(activeSessionId);
    visionWsRef.current = vWs;

    vWs.onopen = () => {
      console.log("Vision WS Connected");
      const interval = setInterval(() => {
        if (vWs.readyState === WebSocket.OPEN) {
          const mockVision = {
            eye_contact_score: 85 + Math.random() * 10,
            engagement_score: 80 + Math.random() * 15,
            yaw: Math.random() * 5,
            pitch: Math.random() * 5,
            roll: 0,
            face_visible: true
          };
          vWs.send(JSON.stringify(mockVision));
          updateVisionMetrics({
            eyeContact: mockVision.eye_contact_score,
            engagement: mockVision.engagement_score,
            faceVisible: mockVision.face_visible
          });
        }
      }, 1000 / 15); // 15fps
      
      vWs._mockInterval = interval;
    };

    return () => {
      if (audioStreamerRef.current) audioStreamerRef.current.stop();
      if (iWs) iWs.close();
      if (vWs) {
        if (vWs._mockInterval) clearInterval(vWs._mockInterval);
        vWs.close();
      }
    };
  }, [activeSessionId, setInterviewState, addInterviewMessage, updateVisionMetrics]);

  return (
    <div className="w-full h-full p-margin-safe lg:p-lg grid grid-cols-1 lg:grid-cols-12 gap-lg relative">
      {/* Left Column: 3D AI Presence */}
      <div className="col-span-1 lg:col-span-5 flex flex-col items-center justify-center relative min-h-[512px] lg:min-h-0 fade-up-stitch delay-100">
        <div className="absolute inset-0 bg-secondary-fixed/5 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="relative w-full aspect-square max-w-[400px] mx-auto z-10 flex flex-col items-center justify-center">
          <div id="threejs-container-ANIMATION_1" ref={threeRef} style={{ width: '100%', height: '100%', position: 'absolute' }}></div>
          <div className="absolute bottom-4 z-10 w-full flex justify-center">
            {interviewState === 'LISTENING' && (
              <div className="flex gap-1 items-center justify-center h-8">
                {[...Array(5)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="w-1 bg-secondary rounded-full"
                    animate={{ height: ['8px', '24px', '8px'] }}
                    transition={{
                      duration: 0.8,
                      repeat: Infinity,
                      delay: i * 0.1,
                      ease: "easeInOut"
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Status Capsule */}
        <div className="mt-lg glass-panel px-md py-xs rounded-full flex items-center gap-sm shadow-[0_0_60px_-15px_rgba(173,198,255,0.15)] z-20">
          <div className="w-2 h-2 rounded-full bg-secondary-container animate-pulse-glow"></div>
          <span className="font-label-mono text-label-mono text-secondary-fixed tracking-widest uppercase">{interviewState}</span>
        </div>
      </div>
      
      {/* Right Column: Telemetry & Transcript */}
      <div className="col-span-1 lg:col-span-7 flex flex-col gap-md h-full lg:max-h-[calc(100vh-96px)]">
        {/* Top Row: Metrics & Vision */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-md flex-shrink-0 fade-up-stitch delay-200">
          {/* SESSION METRICS */}
          <div className="glass-panel rounded-xl p-md flex flex-col justify-between">
            <h2 className="font-label-mono text-label-mono text-on-surface-variant uppercase mb-md">SESSION METRICS</h2>
            <div className="mb-md">
              <span className="font-label-mono text-[10px] text-on-surface-variant uppercase block mb-xs">Fused Confidence</span>
              <div className="flex items-baseline gap-xs">
                <span className="font-display-lg-mobile lg:font-display-lg lg:text-display-lg text-[#10b981] font-light leading-none tracking-tighter">0.0</span>
                <span className="font-label-mono text-label-mono text-on-surface-variant">/ 100</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-sm">
              <div className="border-t border-white/5 pt-xs">
                <span className="font-label-mono text-[10px] text-on-surface-variant uppercase block">Difficulty</span>
                <span className="font-body-md text-body-md text-amber-400">MEDIUM</span>
              </div>
              <div className="border-t border-white/5 pt-xs">
                <span className="font-label-mono text-[10px] text-on-surface-variant uppercase block">Round</span>
                <span className="font-body-md text-body-md text-primary">HR</span>
              </div>
              <div className="border-t border-white/5 pt-xs">
                <span className="font-label-mono text-[10px] text-on-surface-variant uppercase block">Quality</span>
                <span className="font-body-md text-body-md text-primary">HD 1080p</span>
              </div>
              <div className="border-t border-white/5 pt-xs">
                <span className="font-label-mono text-[10px] text-on-surface-variant uppercase block">Latency</span>
                <span className="font-body-md text-body-md text-primary">42ms</span>
              </div>
            </div>
          </div>
          
          {/* VISION TELEMETRY */}
          <div className="glass-panel rounded-xl p-md flex flex-col">
            <h2 className="font-label-mono text-label-mono text-on-surface-variant uppercase mb-md">VISION TELEMETRY</h2>
            <div className="flex items-center gap-sm mb-lg">
              <div className="w-3 h-3 rounded-full border border-[#10b981]/30 bg-[#10b981]/10 flex items-center justify-center">
                <div className={`w-1.5 h-1.5 rounded-full ${visionMetrics.faceVisible ? 'bg-[#10b981]' : 'bg-rose-500'}`}></div>
              </div>
              <span className="font-body-md text-body-md text-primary">Face Visible</span>
            </div>
            <div className="space-y-md mt-auto">
              <div>
                <div className="flex justify-between items-end mb-xs">
                  <span className="font-label-mono text-[10px] text-on-surface-variant uppercase">Eye Contact</span>
                </div>
                <div className="w-full h-[2px] bg-white/5 rounded-full overflow-hidden relative">
                  <div className="absolute top-0 left-0 h-full progress-bar-fill transition-all duration-1000" style={{ width: `${visionMetrics.eyeContact}%` }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-end mb-xs">
                  <span className="font-label-mono text-[10px] text-on-surface-variant uppercase">Engagement</span>
                </div>
                <div className="w-full h-[2px] bg-white/5 rounded-full overflow-hidden relative">
                  <div className="absolute top-0 left-0 h-full progress-bar-fill transition-all duration-1000 delay-300" style={{ width: `${visionMetrics.engagement}%` }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* LIVE TRANSCRIPT */}
        <div className="glass-panel rounded-xl p-md flex-1 flex flex-col min-h-[400px] lg:min-h-0 fade-up-stitch delay-300">
          <div className="flex justify-between items-center mb-md border-b border-white/5 pb-sm flex-shrink-0">
            <h2 className="font-label-mono text-label-mono text-on-surface-variant uppercase">LIVE TRANSCRIPT</h2>
            <span className="material-symbols-outlined text-[16px] text-on-surface-variant">more_horiz</span>
          </div>
          
          <div className="flex-1 overflow-y-auto pr-sm space-y-md">
            {interviewMessages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-on-surface-variant/50 font-label-mono text-label-mono italic">
                No transcript data. Awaiting conversation start...
              </div>
            ) : (
              interviewMessages.map((msg, i) => (
                <div key={i} className={`flex gap-md ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.sender !== 'user' && (
                    <div className="w-8 h-8 rounded-full bg-secondary-container/20 flex items-center justify-center flex-shrink-0 mt-1">
                      <span className="material-symbols-outlined text-secondary text-[16px]">smart_toy</span>
                    </div>
                  )}
                  <div className={`p-sm rounded-xl max-w-[80%] ${msg.sender === 'user' ? 'bg-primary/10 text-primary rounded-tr-sm' : 'bg-surface-container text-on-surface rounded-tl-sm'}`}>
                    <p className="font-transcript text-[16px] leading-relaxed">{msg.content}</p>
                  </div>
                  {msg.sender === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
                      <span className="material-symbols-outlined text-primary text-[16px]">person</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
