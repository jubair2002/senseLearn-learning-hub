"""
Separate routes file for course-related endpoints.
This helps isolate and debug routing issues.
"""
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from src import db
from src.tutor import tutor_bp
from src.auth.models import Course, CourseStudent, CourseRequest, course_tutors, CourseModule, ModuleFile, StudentFileProgress
from src.common.file_utils import allowed_file, generate_unique_filename, get_upload_path, save_uploaded_file, delete_file, get_file_url
import os


@tutor_bp.route('/api/courses/<int:course_id>/view', methods=['GET'])
@login_required
def get_course_view(course_id):
    """API endpoint to get course view HTML content for dashboard."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Get enrolled students
        enrollments = CourseStudent.query.filter_by(course_id=course_id, status='enrolled').all()
        students_data = []
        for enrollment in enrollments:
            student = enrollment.student
            if student:
                students_data.append({
                    'id': student.id,
                    'full_name': student.full_name,
                    'email': student.email,
                    'disability_type': student.disability_type
                })
        
        # Get requests
        requests = CourseRequest.query.filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).order_by(CourseRequest.requested_at.desc()).all()
        
        requests_data = []
        for req in requests:
            try:
                student = req.student
                if student:
                    requests_data.append({
                        'id': req.id,
                        'student_id': student.id,
                        'student_name': student.full_name,
                        'student_email': student.email,
                        'disability_type': student.disability_type,
                        'status': req.status,
                        'requested_at': req.requested_at.isoformat() if req.requested_at else None,
                        'responded_at': req.responded_at.isoformat() if req.responded_at else None
                    })
            except Exception as e:
                from flask import current_app
                current_app.logger.warning(f"Error processing request {req.id}: {str(e)}")
                continue
        
        # Get modules for this course
        modules = CourseModule.query.filter_by(course_id=course_id).order_by(CourseModule.order_index, CourseModule.created_at).all()
        modules_data = []
        for module in modules:
            # Get files for this module
            module_files = ModuleFile.query.filter_by(module_id=module.id).order_by(ModuleFile.uploaded_at).all()
            files_data = []
            for file_obj in module_files:
                files_data.append({
                    'id': file_obj.id,
                    'file_name': file_obj.file_name,
                    'file_path': file_obj.file_path,
                    'file_type': file_obj.file_type,
                    'file_size': file_obj.file_size,
                    'mime_type': file_obj.mime_type,
                    'uploaded_at': file_obj.uploaded_at.isoformat() if file_obj.uploaded_at else None,
                    'url': get_file_url(file_obj.file_path)
                })
            
            modules_data.append({
                'id': module.id,
                'name': module.name,
                'description': module.description or '',
                'order_index': module.order_index,
                'created_at': module.created_at.isoformat() if module.created_at else None,
                'files': files_data,
                'file_count': len(files_data)
            })
        
        # Render course view template
        html = render_template('tutor/course_view.html', 
                              course=course, 
                              students=students_data, 
                              requests=requests_data,
                              modules=modules_data,
                              course_id=course_id)
        
        return jsonify({'success': True, 'html': html}), 200
        
    except Exception as e:
        from flask import current_app
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.exception(f"Error getting course view for {course_id}")
        current_app.logger.error(f"Full traceback: {error_trace}")
        return jsonify({
            'success': False, 
            'error': f'Failed to load course: {str(e)}',
            'details': str(e) if current_app.debug else None
        }), 500


@tutor_bp.route('/api/courses/<int:course_id>/modules', methods=['POST'])
@login_required
def create_module(course_id):
    """API endpoint to create a new module for a course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Verify course exists first
        course = Course.query.get(course_id)
        if not course:
            return jsonify({'success': False, 'error': 'Course not found'}), 404
        
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 403
        
        # Check if request is JSON
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        try:
            data = request.get_json(force=True) or {}
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error parsing JSON: {str(e)}")
            return jsonify({'success': False, 'error': 'Invalid JSON data'}), 400
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Module name is required'}), 400
        
        # Get the highest order_index for this course
        max_order = db.session.query(db.func.max(CourseModule.order_index)).filter_by(course_id=course_id).scalar() or 0
        
        # Create new module
        module = CourseModule(
            course_id=course_id,
            name=name,
            description=description if description else None,
            order_index=max_order + 1,
            created_by=current_user.id
        )
        db.session.add(module)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'module': {
                'id': module.id,
                'name': module.name,
                'description': module.description or '',
                'order_index': module.order_index,
                'created_at': module.created_at.isoformat() if module.created_at else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.exception(f"Error creating module for course {course_id}")
        current_app.logger.error(f"Full traceback: {error_trace}")
        return jsonify({
            'success': False, 
            'error': f'Failed to create module: {str(e)}',
            'details': str(e) if current_app.debug else None
        }), 500


@tutor_bp.route('/api/courses/<int:course_id>/modules', methods=['GET'])
@login_required
def list_modules(course_id):
    """API endpoint to list all modules for a course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        modules = CourseModule.query.filter_by(course_id=course_id).order_by(CourseModule.order_index, CourseModule.created_at).all()
        modules_data = []
        for module in modules:
            file_count = ModuleFile.query.filter_by(module_id=module.id).count()
            modules_data.append({
                'id': module.id,
                'name': module.name,
                'description': module.description or '',
                'order_index': module.order_index,
                'created_at': module.created_at.isoformat() if module.created_at else None,
                'file_count': file_count
            })
        
        return jsonify({'success': True, 'modules': modules_data}), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error listing modules for course {course_id}")
        return jsonify({'success': False, 'error': 'Failed to load modules'}), 500


@tutor_bp.route('/api/modules/<int:module_id>/files', methods=['POST'])
@login_required
def add_file_to_module(module_id):
    """API endpoint to add a file to a module."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Get module and verify tutor is assigned to the course
        module = CourseModule.query.get(module_id)
        if not module:
            return jsonify({'success': False, 'error': 'Module not found'}), 404
        
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=module.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'unknown'
            from src.config import config
            allowed = list(config.ALLOWED_EXTENSIONS) if hasattr(config, 'ALLOWED_EXTENSIONS') else []
            return jsonify({
                'success': False, 
                'error': f'File type not allowed. Extension: .{ext}. Allowed: {", ".join(sorted(allowed))}'
            }), 400
        
        # Generate unique filename for module file
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        from uuid import uuid4
        from werkzeug.utils import secure_filename
        unique_id = str(uuid4())[:8]
        secure_name = secure_filename(file.filename.rsplit('.', 1)[0] if '.' in file.filename else file.filename)
        unique_filename = f"module_{module_id}_{secure_name}_{unique_id}.{ext}" if ext else f"module_{module_id}_{secure_name}_{unique_id}"
        
        # Get upload path (store in courses/{course_id}/modules/{module_id}/)
        from src.config import config
        upload_base = config.UPLOAD_DIR
        module_dir = os.path.join(upload_base, "courses", str(module.course_id), "modules", str(module_id))
        os.makedirs(module_dir, exist_ok=True)
        
        full_path = os.path.join(module_dir, unique_filename)
        relative_path = os.path.join("courses", str(module.course_id), "modules", str(module_id), unique_filename).replace("\\", "/")
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > config.MAX_FILE_SIZE:
            return jsonify({'success': False, 'error': 'File too large'}), 400
        
        # Save file
        file.save(full_path)
        mime_type = file.content_type or 'application/octet-stream'
        
        # Determine file type from extension
        file_type = ext if ext else 'unknown'
        
        # Automatically convert video files to streamable format (fast start)
        video_extensions = {'mp4', 'webm', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'm4v'}
        if ext.lower() in video_extensions:
            try:
                from src.utils.make_video_streamable import make_streamable
                from flask import current_app
                
                # Convert video to streamable format (replaces the file)
                success, converted_path, error = make_streamable(full_path, full_path, logger=current_app.logger)
                
                if success:
                    # Update file size after conversion (may have changed slightly)
                    file_size = os.path.getsize(full_path)
                    current_app.logger.info(f"Video {file.filename} automatically converted to streamable format")
                else:
                    # If conversion fails, continue with original file
                    current_app.logger.warning(f"Video conversion failed for {file.filename}: {error}. Uploading original file.")
            except Exception as e:
                # If conversion fails, continue with original file
                from flask import current_app
                current_app.logger.warning(f"Error during video conversion: {str(e)}. Uploading original file.")
        
        # Create ModuleFile record
        module_file = ModuleFile(
            module_id=module_id,
            file_name=file.filename,
            file_path=relative_path,
            file_type=file_type,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=current_user.id
        )
        db.session.add(module_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'file': {
                'id': module_file.id,
                'file_name': module_file.file_name,
                'file_path': module_file.file_path,
                'file_type': module_file.file_type,
                'file_size': module_file.file_size,
                'mime_type': module_file.mime_type,
                'uploaded_at': module_file.uploaded_at.isoformat() if module_file.uploaded_at else None,
                'url': get_file_url(module_file.file_path)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(f"Error adding file to module {module_id}")
        return jsonify({'success': False, 'error': 'Failed to add file'}), 500


@tutor_bp.route('/api/modules/<int:module_id>/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_module_file(module_id, file_id):
    """API endpoint to delete a file from a module."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Get module file
        module_file = ModuleFile.query.get(file_id)
        if not module_file or module_file.module_id != module_id:
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Get module and verify tutor is assigned to the course
        module = CourseModule.query.get(module_id)
        if not module:
            return jsonify({'success': False, 'error': 'Module not found'}), 404
        
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=module.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete file from filesystem
        delete_file(module_file.file_path)
        
        # Delete from database
        db.session.delete(module_file)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        from flask import current_app
        current_app.logger.exception(f"Error deleting file {file_id} from module {module_id}")
        return jsonify({'success': False, 'error': 'Failed to delete file'}), 500


@tutor_bp.route('/api/modules/<int:module_id>/files', methods=['GET'])
@login_required
def list_module_files(module_id):
    """API endpoint to list all files in a module."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Get module and verify tutor is assigned to the course
        module = CourseModule.query.get(module_id)
        if not module:
            return jsonify({'success': False, 'error': 'Module not found'}), 404
        
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=module.course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        files = ModuleFile.query.filter_by(module_id=module_id).order_by(ModuleFile.uploaded_at).all()
        files_data = []
        for file_obj in files:
            files_data.append({
                'id': file_obj.id,
                'file_name': file_obj.file_name,
                'file_path': file_obj.file_path,
                'file_type': file_obj.file_type,
                'file_size': file_obj.file_size,
                'mime_type': file_obj.mime_type,
                'uploaded_at': file_obj.uploaded_at.isoformat() if file_obj.uploaded_at else None,
                'url': get_file_url(file_obj.file_path)
            })
        
        return jsonify({'success': True, 'files': files_data}), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error listing files for module {module_id}")
        return jsonify({'success': False, 'error': 'Failed to load files'}), 500


@tutor_bp.route('/api/courses/<int:course_id>/students/progress', methods=['GET'])
@login_required
def get_students_progress(course_id):
    """API endpoint for tutors to view all students' progress in a course."""
    if not hasattr(current_user, 'user_type') or current_user.user_type != 'tutor':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        # Verify tutor is assigned to this course
        assignment = db.session.query(course_tutors).filter_by(
            course_id=course_id,
            tutor_id=current_user.id
        ).first()
        
        if not assignment:
            return jsonify({'success': False, 'error': 'Course not found or not assigned'}), 404
        
        # Get all enrolled students
        enrollments = CourseStudent.query.filter_by(
            course_id=course_id,
            status='enrolled'
        ).all()
        
        # Get all files in the course
        modules = CourseModule.query.filter_by(course_id=course_id).order_by(CourseModule.order_index).all()
        total_files = 0
        file_ids = []
        modules_data = {}
        
        for module in modules:
            files = ModuleFile.query.filter_by(module_id=module.id).all()
            file_count = len(files)
            total_files += file_count
            file_ids.extend([f.id for f in files])
            modules_data[module.id] = {
                'name': module.name,
                'file_count': file_count,
                'file_ids': [f.id for f in files]
            }
        
        # Get progress for all students
        students_progress = []
        for enrollment in enrollments:
            student = enrollment.student
            if not student:
                continue
            
            # Get viewed files for this student
            viewed_progress = StudentFileProgress.query.filter(
                StudentFileProgress.student_id == student.id,
                StudentFileProgress.file_id.in_(file_ids)
            ).all()
            
            viewed_count = len(viewed_progress)
            viewed_file_ids = {p.file_id for p in viewed_progress}
            
            # Calculate overall percentage
            percentage = round((viewed_count / total_files * 100) if total_files > 0 else 0, 2)
            
            # Get progress per module
            module_progress_list = []
            for module_id, module_info in modules_data.items():
                module_viewed = sum(1 for fid in module_info['file_ids'] if fid in viewed_file_ids)
                module_total = module_info['file_count']
                module_percentage = round((module_viewed / module_total * 100) if module_total > 0 else 0, 2)
                
                module_progress_list.append({
                    'module_id': module_id,
                    'module_name': module_info['name'],
                    'total_files': module_total,
                    'viewed_files': module_viewed,
                    'percentage': module_percentage
                })
            
            students_progress.append({
                'student_id': student.id,
                'student_name': student.full_name,
                'student_email': student.email,
                'total_files': total_files,
                'viewed_files': viewed_count,
                'percentage': percentage,
                'modules': module_progress_list,
                'enrolled_at': enrollment.assigned_at.isoformat() if enrollment.assigned_at else None
            })
        
        # Sort by percentage descending
        students_progress.sort(key=lambda x: x['percentage'], reverse=True)
        
        return jsonify({
            'success': True,
            'course_id': course_id,
            'total_files': total_files,
            'total_students': len(students_progress),
            'students': students_progress
        }), 200
        
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f"Error getting students progress for course {course_id}")
        return jsonify({'success': False, 'error': 'Failed to get progress'}), 500

