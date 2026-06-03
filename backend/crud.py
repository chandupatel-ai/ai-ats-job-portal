from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import traceback
import models
import schemas
from auth import hash_password  # ✓ CORRECT

def create_user(db: Session, user: schemas.UserCreate):
    try:
        # Check if user already exists
        existing_user = db.query(models.User).filter(
            models.User.email == user.email
        ).first()
        
        if existing_user:
            raise ValueError("Email already registered")
        
        db_user = models.User(
            name=user.name,
            email=user.email,
            password=hash_password(user.password),  # ✓ HASHED
            role=user.role
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
        
    except IntegrityError as e:
        db.rollback()
        print("CRUD_ERROR - Integrity Error:")
        traceback.print_exc()
        raise ValueError("Email already exists")
    
    except Exception as e:
        db.rollback()
        print("CRUD_ERROR:")
        traceback.print_exc()
        raise


# Add this function too (you'll need it for login)
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()