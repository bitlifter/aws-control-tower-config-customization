#!/usr/bin/env python3
"""
AWS Control Tower Config Customization Architecture Diagram Generator

Creates a professional architecture diagram showing the Producer-Consumer Lambda pattern
for the AWS Control Tower Config Customization solution.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch

def create_architecture_diagram():
    """Create and save the architecture diagram"""
    
    # Set up the figure with a professional look
    plt.style.use('default')
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    colors = {
        'aws_orange': '#FF9900',
        'aws_blue': '#146EB4',
        'aws_dark_blue': '#0F2B46',
        'lambda_orange': '#FF9900',
        'eventbridge_purple': '#8C4FFF',
        'sqs_pink': '#FF4B6B',
        'config_green': '#7AA116',
        'light_gray': '#F2F3F3',
        'dark_gray': '#232F3E',
        'arrow_gray': '#545B64'
    }
    
    # Title
    ax.text(8, 9.5, 'AWS Control Tower Config Customization Architecture', 
            fontsize=20, fontweight='bold', ha='center', color=colors['dark_gray'])
    ax.text(8, 9.1, 'Producer-Consumer Lambda Pattern for Config Recorder Updates', 
            fontsize=14, ha='center', color=colors['dark_gray'], style='italic')
    
    # Helper function to create rounded rectangles with text
    def create_component(x, y, width, height, text, color, text_color='white', fontsize=10):
        """Create a component box with text"""
        box = FancyBboxPatch((x, y), width, height,
                           boxstyle="round,pad=0.1",
                           facecolor=color,
                           edgecolor='white',
                           linewidth=2)
        ax.add_patch(box)
        
        # Add text
        ax.text(x + width/2, y + height/2, text,
                ha='center', va='center', fontsize=fontsize, 
                fontweight='bold', color=text_color, wrap=True)
    
    # Helper function to create arrows
    def create_arrow(start_x, start_y, end_x, end_y, text='', offset_text=0.3):
        """Create an arrow with optional text"""
        arrow = ConnectionPatch((start_x, start_y), (end_x, end_y), 
                              "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc=colors['arrow_gray'],
                              ec=colors['arrow_gray'], linewidth=2)
        ax.add_patch(arrow)
        
        if text:
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2 + offset_text
            ax.text(mid_x, mid_y, text, ha='center', va='center', 
                   fontsize=9, fontweight='bold', color=colors['dark_gray'],
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor='none', alpha=0.8))
    
    # Layer 1: Control Tower Events (Top)
    create_component(1, 7.5, 4, 1.2, 'AWS Control Tower\nLifecycle Events\n\n• CreateManagedAccount\n• UpdateManagedAccount\n• UpdateLandingZone', 
                    colors['aws_blue'], fontsize=9)
    
    create_component(6, 7.5, 4, 1.2, 'Amazon EventBridge\n\nEvent Routing & Filtering\n\n• Rule-based routing\n• Event pattern matching', 
                    colors['eventbridge_purple'], fontsize=9)
    
    # Layer 2: Producer Lambda (Middle-Upper)
    create_component(11, 7.5, 4, 1.2, 'Producer Lambda\n(Event Handler)\n\n• Receives CT events\n• Filters excluded accounts\n• Sends to SQS queue', 
                    colors['lambda_orange'], fontsize=9)
    
    # Layer 3: SQS Queue (Middle)
    create_component(6, 5, 4, 1.2, 'Amazon SQS Queue\n(Message Buffer)\n\n• Reliable message delivery\n• Retry logic & DLQ\n• Decouples processing', 
                    colors['sqs_pink'], fontsize=9)
    
    # Layer 4: Consumer Lambda (Middle-Lower)
    create_component(11, 5, 4, 1.2, 'Consumer Lambda\n(Config Updater)\n\n• Processes SQS messages\n• Assumes CT execution role\n• Updates Config recorders', 
                    colors['lambda_orange'], fontsize=9)
    
    # Layer 5: Target Accounts (Bottom)
    create_component(1, 2.5, 3, 1.2, 'Management Account\n891377069955\n\n[X] Excluded',
                    colors['light_gray'], text_color=colors['dark_gray'], fontsize=9)
    
    create_component(5, 2.5, 3, 1.2, 'Log Archive Account\n058264522153\n\n[X] Excluded',
                    colors['light_gray'], text_color=colors['dark_gray'], fontsize=9)
    
    create_component(9, 2.5, 3, 1.2, 'Audit Account\n211125586359\n\n[X] Excluded',
                    colors['light_gray'], text_color=colors['dark_gray'], fontsize=9)
    
    create_component(13, 2.5, 2.5, 1.2, 'Managed Accounts\n(Multiple)\n\n[✓] Updated',
                    colors['config_green'], fontsize=9)
    
    # Arrows showing the flow
    # Control Tower -> EventBridge
    create_arrow(5, 8.1, 6, 8.1, 'Events')
    
    # EventBridge -> Producer Lambda
    create_arrow(10, 8.1, 11, 8.1, 'Trigger')
    
    # Producer Lambda -> SQS (curved down)
    create_arrow(13, 7.5, 8, 6.2, 'Queue\nMessage')
    
    # SQS -> Consumer Lambda
    create_arrow(10, 5.6, 11, 5.6, 'Process')
    
    # Consumer Lambda -> Target Accounts (multiple arrows)
    create_arrow(13, 5, 14.25, 3.7, 'Config\nUpdates')
    
    # Add excluded accounts indicators (dashed lines)
    for x_pos in [2.5, 6.5, 10.5]:
        ax.plot([13, x_pos], [5, 3.7], '--', color=colors['arrow_gray'], alpha=0.5, linewidth=1)
    
    # Add legend/key
    legend_y = 1.5
    ax.text(1, legend_y, 'Key Components:', fontsize=12, fontweight='bold', color=colors['dark_gray'])
    
    legend_items = [
        ('Producer Pattern', colors['lambda_orange']),
        ('Event Processing', colors['eventbridge_purple']),
        ('Message Queue', colors['sqs_pink']),
        ('Config Updates', colors['config_green']),
        ('Excluded Accounts', colors['light_gray'])
    ]
    
    for i, (label, color) in enumerate(legend_items):
        x_offset = 3 * i
        small_box = FancyBboxPatch((1 + x_offset, 0.8), 0.3, 0.3,
                                 boxstyle="round,pad=0.05",
                                 facecolor=color,
                                 edgecolor='white',
                                 linewidth=1)
        ax.add_patch(small_box)
        text_color = 'white' if color != colors['light_gray'] else colors['dark_gray']
        ax.text(1.4 + x_offset, 0.6, label, fontsize=9, color=colors['dark_gray'])
    
    # Add flow indicators
    ax.text(8, 0.3, 'Flow: Control Tower Events → EventBridge → Producer Lambda → SQS Queue → Consumer Lambda → Target Accounts', 
            ha='center', fontsize=11, style='italic', color=colors['dark_gray'],
            bbox=dict(boxstyle="round,pad=0.3", facecolor=colors['light_gray'], edgecolor='none', alpha=0.8))
    
    # Save the diagram
    plt.tight_layout()
    plt.savefig('aws-control-tower-config-architecture.png',
                dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.savefig('aws-control-tower-config-architecture.svg',
                format='svg', bbox_inches='tight', facecolor='white', edgecolor='none')
    
    print("[✓] Architecture diagram created successfully!")
    print("   - PNG: aws-control-tower-config-architecture.png")
    print("   - SVG: aws-control-tower-config-architecture.svg")
    
    # Close the plot instead of showing it (for headless operation)
    plt.close()

if __name__ == "__main__":
    create_architecture_diagram()