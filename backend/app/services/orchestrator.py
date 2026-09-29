"""
Orchestrator Service — Milestone 7.

Orchestrates the entire AI generation pipeline asynchronously in the background.
Connects ContentPlanner, ImageGenerator, TTSGenerator, TranscriptionService, and VideoCompositor.
Updates JobStore state as it progresses.
"""

import asyncio
import logging

from app.services.job_store import job_store
from app.services.content_planner import generate_content_plan
from app.services.image_generator import image_generator, TEMP_ASSETS_DIR
from app.services.tts_generator import tts_generator
from app.services.transcription_service import transcription_service
from app.services.video_compositor import video_compositor

logger = logging.getLogger(__name__)


async def run_generation_pipeline(job_id: str, topic: str, duration: int, style: str) -> None:
    """
    Executes the full pipeline for a given job, updating the job store at each stage.
    """
    logger.info("Starting pipeline for job %s (topic: %s)", job_id, topic)
    try:
        # ---------------------------------------------------------
        # Step 1: Planning
        # ---------------------------------------------------------
        job_store.update_job(job_id, status="processing", stage="planning", progress=10)
        
        # generate_content_plan is synchronous, wrap in thread
        content_plan = await asyncio.to_thread(generate_content_plan, topic, duration, style)
        
        # Save initial plan data
        scenes_data = [
            {
                "scene_id": s.scene_id,
                "narration": s.narration,
                "visual_prompt": s.visual_prompt,
                "duration": s.duration
            }
            for s in content_plan.scenes
        ]
        
        job_store.update_job(
            job_id,
            title=content_plan.title,
            hook=content_plan.hook,
            script=content_plan.script,
            scenes=scenes_data
        )
        
        # ---------------------------------------------------------
        # Step 2: Generating Assets
        # ---------------------------------------------------------
        job_store.update_job(job_id, stage="generating_assets")
        
        asset_scenes = []
        total_scenes = len(content_plan.scenes)
        
        for idx, scene in enumerate(content_plan.scenes):
            scene_id = scene.scene_id
            
            # Generate Image (sync network call wrapped in thread)
            image_path = await asyncio.to_thread(
                image_generator.generate_scene_image, job_id, scene_id, scene.visual_prompt
            )
            
            # Generate Audio (async native)
            audio_path = await tts_generator.generate_scene_audio(job_id, scene_id, scene.narration)
            
            # Generate Subtitles (sync model execution wrapped in thread)
            srt_path = await asyncio.to_thread(
                transcription_service.generate_scene_srt, job_id, scene_id, audio_path
            )
            
            asset_scenes.append({
                "scene_id": scene_id,
                "image_path": image_path,
                "audio_path": audio_path,
                "srt_path": srt_path
            })
            
            # Progress updates smoothly from 10% to 80%
            progress = 10 + int(((idx + 1) / total_scenes) * 70)
            job_store.update_job(job_id, progress=progress)

        # ---------------------------------------------------------
        # Step 3: Compositing
        # ---------------------------------------------------------
        job_store.update_job(job_id, stage="compositing", progress=80)
        final_mp4_path = await asyncio.to_thread(
            video_compositor.build_video_from_assets, job_id, asset_scenes
        )

        # ---------------------------------------------------------
        # Step 4: Complete
        # ---------------------------------------------------------
        job_store.update_job(
            job_id, 
            status="completed", 
            stage="completed",
            progress=100, 
            video_url=final_mp4_path
        )
        
        logger.info("Job %s completed successfully: %s", job_id, final_mp4_path)

    except Exception as exc:
        logger.error("Job %s failed: %s", job_id, exc)
        job_store.update_job(job_id, status="failed", error=str(exc))


async def regenerate_scene_pipeline(job_id: str, scene_id: int) -> None:
    """
    Regenerates the image for a specific scene and reconstructs the final video
    without re-running the LLM or TTS steps.
    """
    logger.info("Starting regeneration for job %s scene %d", job_id, scene_id)
    try:
        job = job_store.get_job(job_id)
        if not job or job.get("status") != "completed":
            raise ValueError(f"Job {job_id} not found or not completed.")

        job_store.update_job(job_id, status="processing", stage="regenerating_scene")
        
        scenes = job.get("scenes", [])
        target_scene = next((s for s in scenes if s["scene_id"] == scene_id), None)
        if not target_scene:
            raise ValueError(f"Scene {scene_id} not found in job {job_id}.")
            
        visual_prompt = target_scene["visual_prompt"]
        
        # 1. Regenerate image
        await asyncio.to_thread(
            image_generator.generate_scene_image, job_id, scene_id, visual_prompt
        )
        
        # 2. Reconstruct asset_scenes
        asset_scenes = []
        for s in scenes:
            sid = s["scene_id"]
            asset_scenes.append({
                "scene_id": sid,
                "image_path": str((TEMP_ASSETS_DIR / f"{job_id}_scene_{sid}.png").resolve()),
                "audio_path": str((TEMP_ASSETS_DIR / f"{job_id}_scene_{sid}.mp3").resolve()),
                "srt_path": str((TEMP_ASSETS_DIR / f"{job_id}_scene_{sid}.srt").resolve())
            })
            
        # 3. Compositing
        final_mp4_path = await asyncio.to_thread(
            video_compositor.build_video_from_assets, job_id, asset_scenes
        )
        
        job_store.update_job(
            job_id,
            status="completed",
            stage="completed",
            progress=100,
            video_url=final_mp4_path
        )
        
        logger.info("Regeneration for job %s scene %d completed.", job_id, scene_id)
        
    except Exception as exc:
        logger.error("Regeneration for job %s scene %d failed: %s", job_id, scene_id, exc)
        job_store.update_job(job_id, status="failed", error=str(exc))
