"use client";

import { motion } from "framer-motion";

export default function Footer() {
  return (
    <motion.footer 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full py-8 mt-auto border-t border-gray-200 dark:border-gray-800 glass"
    >
      <div className="container mx-auto px-4 flex justify-center items-center">
        <p className="text-sm font-medium text-gray-600 dark:text-gray-300 flex items-center gap-2">
          Made by Priyam Parashar <span className="heart text-red-500 text-lg">❤️</span>
        </p>
      </div>
    </motion.footer>
  );
}
