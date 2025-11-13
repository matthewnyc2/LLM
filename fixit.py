#!/usr/bin/env python3
"""Script to ensure main2.py properly handles launching in different modes."""

import re

# Read the original file
with open('main2.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure the launch_llm function both updates config AND launches the LLM
launch_llm_replacement = '''def launch_llm(llms: List[LLMTemplate], all_servers: Dict[str, object], config: Dict[str, object]) -> None:
    """Update configuration and launch the selected LLM."""
    selected_llm_filename = config.get("selected_llm")
    if not selected_llm_filename:
        print("\\nNo LLM selected. Please select an LLM first.")
        input("Press Enter to continue...")
        return
    
    # Find the selected LLM template
    selected_llm = None
    for llm in llms:
        if llm.filename == selected_llm_filename:
            selected_llm = llm
            break
    
    if not selected_llm:
        print(f"\\nError: Could not find LLM template for {selected_llm_filename}")
        input("Press Enter to continue...")
        return
    
    # Get selected servers
    selected_server_names = config.get("selected_mcp_servers", [])
    if not selected_server_names:
        print("\\nNo MCP servers selected. Launching with empty configuration.")
    
    # Build server configuration with only selected servers
    server_config = {}
    for server_name in selected_server_names:
        if server_name in all_servers:
            server_config[server_name] = all_servers[server_name]
    
    # Generate configuration
    output_directory = Path(CONFIG_DIR) / config.get("output_directory", "generated")
    output_directory.mkdir(parents=True, exist_ok=True)
    
    output_path = output_directory / selected_llm.filename
    document = selected_llm.render(server_config)
    
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write(document)
    
    # Copy to app-specific location
    location_type = config.get("location_type", "windows")
    locations = APP_LOCATIONS.get(location_type, {})
    
    if selected_llm.filename in locations:
        app_location_raw = locations[selected_llm.filename]
        app_location = Path(os.path.expandvars(app_location_raw))
        app_location.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(output_path, app_location)
            print(f"\\nConfiguration updated at: {app_location}")
        except Exception as exc:
            print(f"\\nFailed to copy configuration: {exc}")
    
    # Launch the LLM interactively
    cmd = CLI_LAUNCH_COMMANDS.get(selected_llm.filename)
    if not cmd:
        print(f"\\nNo launch command configured for {selected_llm.display_name}")
        input("Press Enter to continue...")
        return
    
    print(f"\\nLaunching {selected_llm.display_name}...")
    log_history("launch_llm", {
        "llm": selected_llm.filename,
        "servers": selected_server_names,
        "command": cmd
    })
    
    try:
        # Launch interactively (wait for it to complete)
        if sys.platform == "win32":
            # Use subprocess.run for interactive mode on Windows
            result = subprocess.run(cmd, shell=True)
            if result.returncode != 0:
                print(f"\\n{selected_llm.display_name} exited with code {result.returncode}")
        else:
            # On Unix-like systems, launch interactively
            result = subprocess.run([cmd])
            if result.returncode != 0:
                print(f"\\n{selected_llm.display_name} exited with code {result.returncode}")
    except FileNotFoundError:
        print(f"\\nCommand not found: {cmd}")
        print("Make sure the application is installed and in your PATH.")
    except Exception as exc:
        print(f"\\nFailed to launch: {exc}")
    
    input("\\nPress Enter to continue...")'''

# Find and replace the launch_llm function
start_marker = 'def launch_llm(llms: List[LLMTemplate], all_servers: Dict[str, object], config: Dict[str, object]) -> None:'
start_idx = content.find(start_marker)

if start_idx != -1:
    # Find the end of the function
    temp_idx = content.find('\n\ndef ', start_idx + 1)
    if temp_idx == -1:
        temp_idx = len(content)
    
    func_content = content[start_idx:temp_idx]
    last_input_idx = func_content.rfind('    input("\\nPress Enter to continue...")')
    
    if last_input_idx != -1:
        actual_end = start_idx + last_input_idx + len('    input("\\nPress Enter to continue...")')
        content = content[:start_idx] + launch_llm_replacement + content[actual_end:]

# Update batch_commands to ensure it runs in non-interactive batch mode
batch_commands_replacement = '''def batch_commands(llms: List[LLMTemplate], all_servers: Dict[str, object], config: Dict[str, object]) -> None:
    """Batch command execution mode - non-interactive."""
    print("\\n=== Batch Commands ===")
    print("Enter a command to execute in batch mode (non-interactive).")
    print("Press Enter without a command to return to main menu.\\n")
    
    while True:
        cmd = input("Enter command (or press Enter to exit): ").strip()
        if not cmd:
            break
        
        # Get last used LLM or current selection as default
        default_llm_filename = config.get("last_batch_llm") or config.get("selected_llm")
        default_llm = None
        default_index = None
        
        if default_llm_filename:
            for idx, llm in enumerate(llms):
                if llm.filename == default_llm_filename:
                    default_llm = llm
                    default_index = idx
                    break
        
        # Show LLM selection
        print("\\nSelect LLM to execute command:")
        for idx, llm in enumerate(llms, start=1):
            marker = f" (press Enter for this)" if default_llm and llm.filename == default_llm.filename else ""
            print(f"  {idx}. {llm.display_name}{marker}")
        
        if default_llm:
            choice = input(f"\\nSelect LLM [default: {default_llm.display_name}]: ").strip()
        else:
            choice = input("\\nSelect LLM: ").strip()
        
        # Process selection
        selected_llm = None
        if not choice and default_llm:
            selected_llm = default_llm
        elif choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(llms):
                selected_llm = llms[index - 1]
        
        if not selected_llm:
            print("Invalid selection. Command cancelled.")
            continue
        
        # Save as last batch LLM
        config["last_batch_llm"] = selected_llm.filename
        save_config(config)
        
        # Get selected servers and generate config
        selected_server_names = config.get("selected_mcp_servers", [])
        server_config = {}
        for server_name in selected_server_names:
            if server_name in all_servers:
                server_config[server_name] = all_servers[server_name]
        
        # Generate and deploy configuration
        output_directory = Path(CONFIG_DIR) / config.get("output_directory", "generated")
        output_directory.mkdir(parents=True, exist_ok=True)
        output_path = output_directory / selected_llm.filename
        
        document = selected_llm.render(server_config)
        with output_path.open("w", encoding="utf-8") as handle:
            handle.write(document)
        
        # Copy to app location
        location_type = config.get("location_type", "windows")
        locations = APP_LOCATIONS.get(location_type, {})
        
        if selected_llm.filename in locations:
            app_location_raw = locations[selected_llm.filename]
            app_location = Path(os.path.expandvars(app_location_raw))
            app_location.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(output_path, app_location)
                print(f"Configuration deployed to: {app_location}")
            except Exception as exc:
                print(f"Failed to copy configuration: {exc}")
        
        # Execute command in batch mode (non-interactive, capture output)
        print(f"\\nExecuting in batch mode with {selected_llm.display_name}: {cmd}")
        log_history("batch_command", {
            "llm": selected_llm.filename,
            "command": cmd,
            "servers": selected_server_names
        })
        
        try:
            # Run in batch mode - capture output and don't interact
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout for batch commands
            )
            
            # Display output
            if result.stdout:
                print("\\n--- Output ---")
                print(result.stdout)
            if result.stderr:
                print("\\n--- Errors ---")
                print(result.stderr)
            
            if result.returncode != 0:
                print(f"\\nCommand exited with code {result.returncode}")
            else:
                print("\\nCommand completed successfully.")
                
        except subprocess.TimeoutExpired:
            print("\\nCommand timed out after 5 minutes.")
        except Exception as exc:
            print(f"\\nError executing command: {exc}")
        
        print()'''

# Find and replace the batch_commands function
start_marker = 'def batch_commands(llms: List[LLMTemplate], all_servers: Dict[str, object], config: Dict[str, object]) -> None:'
start_idx = content.find(start_marker)

if start_idx != -1:
    # Find the end of the function
    temp_idx = content.find('\n\ndef ', start_idx + 1)
    if temp_idx == -1:
        # Check if it's near the end before main_menu
        temp_idx = content.find('\n\ndef main_menu(')
    if temp_idx == -1:
        temp_idx = len(content)
    
    func_content = content[start_idx:temp_idx]
    # Find the last print() statement in the function
    last_print_idx = func_content.rfind('        print()')
    
    if last_print_idx != -1:
        actual_end = start_idx + last_print_idx + len('        print()')
        content = content[:start_idx] + batch_commands_replacement + content[actual_end:]

# Ensure menu shows "Launch LLM" not "Update LLM Config"
content = content.replace('print("  3. Update LLM Config")', 'print("  3. Launch LLM")')

# Add subprocess import if not present
if 'import subprocess' not in content:
    # Add after other imports
    import_idx = content.find('import sys')
    if import_idx != -1:
        end_of_line = content.find('\n', import_idx)
        content = content[:end_of_line] + '\nimport subprocess' + content[end_of_line:]

# Write the modified content back
with open('main2.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully modified main2.py:")
print("- launch_llm: Updates config and launches LLM interactively (waits for completion)")
print("- batch_commands: Executes commands in non-interactive batch mode with output capture")
print("- Menu option 3 shows 'Launch LLM'")
print("- Batch mode now captures output and has a 5-minute timeout")