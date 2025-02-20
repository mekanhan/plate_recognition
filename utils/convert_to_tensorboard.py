import pandas as pd
import tensorflow as tf
import os

# Path to CSV file
csv_path = "runs/detect/train13/results.csv"

# Load CSV
df = pd.read_csv(csv_path)

# Set up TensorBoard writer
log_dir = "runs/detect/train13/tb_logs"
writer = tf.summary.create_file_writer(log_dir)

# Log each epoch's results
with writer.as_default():
    for i, row in df.iterrows():
        tf.summary.scalar("train/box_loss", row["train/box_loss"], step=row["epoch"])
        tf.summary.scalar("train/cls_loss", row["train/cls_loss"], step=row["epoch"])
        tf.summary.scalar("train/dfl_loss", row["train/dfl_loss"], step=row["epoch"])
        
        tf.summary.scalar("metrics/precision", row["metrics/precision(B)"], step=row["epoch"])
        tf.summary.scalar("metrics/recall", row["metrics/recall(B)"], step=row["epoch"])
        tf.summary.scalar("metrics/mAP50", row["metrics/mAP50(B)"], step=row["epoch"])
        tf.summary.scalar("metrics/mAP50-95", row["metrics/mAP50-95(B)"], step=row["epoch"])
        
        tf.summary.scalar("val/box_loss", row["val/box_loss"], step=row["epoch"])
        tf.summary.scalar("val/cls_loss", row["val/cls_loss"], step=row["epoch"])
        tf.summary.scalar("val/dfl_loss", row["val/dfl_loss"], step=row["epoch"])

        tf.summary.scalar("lr/pg0", row["lr/pg0"], step=row["epoch"])
        tf.summary.scalar("lr/pg1", row["lr/pg1"], step=row["epoch"])
        tf.summary.scalar("lr/pg2", row["lr/pg2"], step=row["epoch"])
        
        writer.flush()

print("✅ TensorBoard logs created successfully!")
