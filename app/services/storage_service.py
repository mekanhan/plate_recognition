    """Add enhanced results to the database"""
    if not results:
        logger.debug("No enhanced results to add")
        return

    if not self.initialization_complete:
        logger.warning("Attempted to add enhanced results before initialization complete")
        return

    async with self.storage_lock:
        logger.debug(f"Adding {len(results)} enhanced results to database")

        # Add timestamp and ID if missing
        for result in results:
            if "timestamp" not in result:
                result["timestamp"] = time.time()

            if "enhanced_id" not in result:
                result["enhanced_id"] = f"enh-{str(uuid.uuid4())}"

            if "enhanced_at" not in result:
                result["enhanced_at"] = time.time()

        self.enhanced_database["enhanced_results"].extend(results)
        logger.debug(f"Total enhanced results in database: {len(self.enhanced_database['enhanced_results'])}")

        # Force save immediately after adding enhanced results
        await self._save_data()

        # Log details of first result for debugging
        if results:
            first_result = results[0]
            logger.info(f"Added enhanced result: ID={first_result.get('enhanced_id', 'unknown')}, "
                       f"Plate={first_result.get('plate_text', 'unknown')}, "
                       f"Confidence={first_result.get('confidence', 0)}")

